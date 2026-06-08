import Foundation

struct APIClient: Sendable {
    let baseURL: URL
    let session: URLSession

    init(
        baseURL: URL = URL(string: "http://192.168.178.31")!,
        session: URLSession = .shared
    ) {
        self.baseURL = baseURL
        self.session = session
    }

    func fetch<T: Decodable>(_ endpoint: String, method: String = "GET", body: Encodable? = nil) async throws -> T {
        let url = try url(for: endpoint)
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Accept")

        if let body {
            request.setValue("application/json; charset=utf-8", forHTTPHeaderField: "Content-Type")
            request.httpBody = try JSONEncoder().encode(AnyEncodable(body))
        }

        return try await perform(request)
    }

    func uploadAttachments(
        orderID: Int,
        files: [UploadableFile],
        documentType: String,
        orderContext: String
    ) async throws -> AttachmentUploadResponse {
        guard !files.isEmpty else {
            throw APIError.multipartEncoding
        }

        let boundary = "BenchFlowBoundary-\(UUID().uuidString)"
        let url = try url(for: "/api/orders/\(orderID)/attachments")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        request.setValue("application/json", forHTTPHeaderField: "Accept")

        var body = Data()
        body.appendMultipartField(named: "document_type", value: documentType, boundary: boundary)
        body.appendMultipartField(named: "document_context", value: orderContext, boundary: boundary)

        for file in files {
            body.appendMultipartFile(named: "order_files", file: file, boundary: boundary)
        }

        body.appendString("--\(boundary)--\r\n")
        request.httpBody = body
        return try await perform(request)
    }

    func deleteAttachment(orderID: Int, mediaID: Int) async throws -> DeleteAttachmentResponse {
        try await fetch("/api/orders/\(orderID)/attachments/\(mediaID)", method: "DELETE")
    }

    private func url(for endpoint: String) throws -> URL {
        if let absolute = URL(string: endpoint), absolute.scheme != nil {
            return absolute
        }
        let trimmed = endpoint.hasPrefix("/") ? String(endpoint.dropFirst()) : endpoint
        guard let url = URL(string: trimmed, relativeTo: baseURL)?.absoluteURL else {
            throw APIError.invalidURL
        }
        return url
    }

    private func perform<T: Decodable>(_ request: URLRequest) async throws -> T {
        do {
            let (data, response) = try await session.data(for: request)
            guard let httpResponse = response as? HTTPURLResponse else {
                throw APIError.invalidResponse
            }

            guard (200 ... 299).contains(httpResponse.statusCode) else {
                let message = parseErrorMessage(from: data)
                throw APIError.httpStatus(httpResponse.statusCode, message)
            }

            do {
                return try decoder.decode(T.self, from: data)
            } catch {
                throw APIError.decoding(error.localizedDescription)
            }
        } catch let error as APIError {
            throw error
        } catch {
            throw APIError.transport(error.localizedDescription)
        }
    }

    private func parseErrorMessage(from data: Data) -> String {
        guard !data.isEmpty else { return "" }
        if let payload = try? decoder.decode(APIErrorPayload.self, from: data) {
            return payload.error
        }
        return String(data: data, encoding: .utf8) ?? ""
    }

    private var decoder: JSONDecoder {
        let decoder = JSONDecoder()
        let timestampFormatter = DateFormatter()
        timestampFormatter.locale = Locale(identifier: "en_US_POSIX")
        timestampFormatter.dateFormat = "yyyy-MM-dd HH:mm:ss"

        let dateOnlyFormatter = DateFormatter()
        dateOnlyFormatter.locale = Locale(identifier: "en_US_POSIX")
        dateOnlyFormatter.dateFormat = "yyyy-MM-dd"

        decoder.dateDecodingStrategy = .custom { container in
            let value = try container.singleValueContainer().decode(String.self)
            if let timestamp = timestampFormatter.date(from: value) {
                return timestamp
            }
            if let dateOnly = dateOnlyFormatter.date(from: value) {
                return dateOnly
            }
            throw DecodingError.dataCorruptedError(in: container, debugDescription: "Unsupported date format: \(value)")
        }
        return decoder
    }
}

private struct AnyEncodable: Encodable {
    private let encodeClosure: (Encoder) throws -> Void

    init(_ wrapped: Encodable) {
        encodeClosure = { encoder in
            try wrapped.encode(to: encoder)
        }
    }

    func encode(to encoder: Encoder) throws {
        try encodeClosure(encoder)
    }
}

private extension Data {
    mutating func appendString(_ string: String) {
        if let data = string.data(using: .utf8) {
            append(data)
        }
    }

    mutating func appendMultipartField(named name: String, value: String, boundary: String) {
        appendString("--\(boundary)\r\n")
        appendString("Content-Disposition: form-data; name=\"\(name)\"\r\n\r\n")
        appendString(value)
        appendString("\r\n")
    }

    mutating func appendMultipartFile(named name: String, file: UploadableFile, boundary: String) {
        appendString("--\(boundary)\r\n")
        appendString("Content-Disposition: form-data; name=\"\(name)\"; filename=\"\(file.filename)\"\r\n")
        appendString("Content-Type: \(file.mime_type)\r\n\r\n")
        append(file.data)
        appendString("\r\n")
    }
}
