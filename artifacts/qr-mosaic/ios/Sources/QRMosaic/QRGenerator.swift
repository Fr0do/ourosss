import CoreImage
import UIKit

public enum QRErrorCorrection: String {
    case low = "L"
    case medium = "M"
    case quartile = "Q"
    case high = "H"
}

public struct QRGenerator {
    public init() {}

    public func generate(
        data: String,
        size: CGFloat = 512,
        errorCorrection: QRErrorCorrection = .high
    ) -> UIImage? {
        guard let filter = CIFilter(name: "CIQRCodeGenerator") else { return nil }
        filter.setValue(data.data(using: .utf8), forKey: "inputMessage")
        filter.setValue(errorCorrection.rawValue, forKey: "inputCorrectionLevel")

        guard let ciImage = filter.outputImage else { return nil }

        let scale = size / ciImage.extent.size.width
        let transformed = ciImage.transformed(by: CGAffineTransform(scaleX: scale, y: scale))

        let context = CIContext()
        guard let cgImage = context.createCGImage(transformed, from: transformed.extent) else {
            return nil
        }
        return UIImage(cgImage: cgImage)
    }

    public func generatePNGData(
        data: String,
        size: CGFloat = 512,
        errorCorrection: QRErrorCorrection = .high
    ) -> Data? {
        generate(data: data, size: size, errorCorrection: errorCorrection)?.pngData()
    }
}
