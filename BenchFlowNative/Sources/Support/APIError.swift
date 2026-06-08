import Foundation

enum APIError: Error, LocalizedError, Equatable, Sendable {
    case invalidURL
    case invalidResponse
    case httpStatus(Int, String)
    case decoding(String)
    case transport(String)
    case multipartEncoding

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Die Server-URL ist ungueltig."
        case .invalidResponse:
            return "Die Server-Antwort war ungueltig."
        case let .httpStatus(code, message):
            return message.isEmpty ? "Der Server hat mit Status \(code) geantwortet." : message
        case let .decoding(message):
            return "Die Antwort konnte nicht gelesen werden: \(message)"
        case let .transport(message):
            return message
        case .multipartEncoding:
            return "Der Upload konnte nicht vorbereitet werden."
        }
    }
}
