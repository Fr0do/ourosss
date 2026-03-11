import CoreImage
import UIKit

public enum MosaicStyle {
    case overlay
    case halftone
    case artistic
}

public struct MosaicBlender {
    public init() {}

    public func blend(
        qrImage: UIImage,
        background: UIImage,
        opacity: CGFloat = 0.5,
        style: MosaicStyle = .overlay
    ) -> UIImage? {
        let size = background.size
        let renderer = UIGraphicsImageRenderer(size: size)

        return renderer.image { context in
            background.draw(in: CGRect(origin: .zero, size: size))

            switch style {
            case .overlay:
                blendOverlay(qrImage: qrImage, in: context, size: size, opacity: opacity)
            case .halftone:
                blendHalftone(qrImage: qrImage, background: background, in: context, size: size)
            case .artistic:
                blendArtistic(qrImage: qrImage, background: background, in: context, size: size, opacity: opacity)
            }
        }
    }

    private func blendOverlay(
        qrImage: UIImage,
        in context: UIGraphicsImageRendererContext,
        size: CGSize,
        opacity: CGFloat
    ) {
        qrImage.draw(
            in: CGRect(origin: .zero, size: size),
            blendMode: .normal,
            alpha: opacity
        )
    }

    private func blendHalftone(
        qrImage: UIImage,
        background: UIImage,
        in context: UIGraphicsImageRendererContext,
        size: CGSize
    ) {
        guard let cgQR = qrImage.cgImage else { return }

        let moduleCount = detectModuleCount(cgImage: cgQR)
        let moduleW = size.width / CGFloat(moduleCount)
        let moduleH = size.height / CGFloat(moduleCount)

        let qrPixels = getPixelData(cgImage: cgQR)

        for row in 0..<moduleCount {
            for col in 0..<moduleCount {
                let px = col * cgQR.width / moduleCount + cgQR.width / (2 * moduleCount)
                let py = row * cgQR.height / moduleCount + cgQR.height / (2 * moduleCount)
                let idx = (py * cgQR.width + px) * 4
                let isDark = idx < qrPixels.count && qrPixels[idx] < 128

                let rect = CGRect(
                    x: CGFloat(col) * moduleW,
                    y: CGFloat(row) * moduleH,
                    width: moduleW,
                    height: moduleH
                )

                let overlayColor = isDark
                    ? UIColor.black.withAlphaComponent(0.6)
                    : UIColor.white.withAlphaComponent(0.4)
                overlayColor.setFill()
                context.fill(rect)
            }
        }
    }

    private func blendArtistic(
        qrImage: UIImage,
        background: UIImage,
        in context: UIGraphicsImageRendererContext,
        size: CGSize,
        opacity: CGFloat
    ) {
        guard let cgBg = background.cgImage, let cgQR = qrImage.cgImage else { return }

        let bgPixels = getPixelData(cgImage: cgBg)
        let avgColor = averageColor(pixels: bgPixels)

        let darkColor = UIColor(
            red: avgColor.0 * 0.3,
            green: avgColor.1 * 0.3,
            blue: avgColor.2 * 0.3,
            alpha: opacity
        )
        let lightColor = UIColor(
            red: min(1.0, avgColor.0 * 1.5),
            green: min(1.0, avgColor.1 * 1.5),
            blue: min(1.0, avgColor.2 * 1.5),
            alpha: opacity * 0.3
        )

        let moduleCount = detectModuleCount(cgImage: cgQR)
        let moduleW = size.width / CGFloat(moduleCount)
        let moduleH = size.height / CGFloat(moduleCount)
        let qrPixels = getPixelData(cgImage: cgQR)

        for row in 0..<moduleCount {
            for col in 0..<moduleCount {
                let px = col * cgQR.width / moduleCount + cgQR.width / (2 * moduleCount)
                let py = row * cgQR.height / moduleCount + cgQR.height / (2 * moduleCount)
                let idx = (py * cgQR.width + px) * 4
                let isDark = idx < qrPixels.count && qrPixels[idx] < 128

                let rect = CGRect(
                    x: CGFloat(col) * moduleW,
                    y: CGFloat(row) * moduleH,
                    width: moduleW,
                    height: moduleH
                )

                (isDark ? darkColor : lightColor).setFill()
                context.fill(rect)
            }
        }
    }

    private func detectModuleCount(cgImage: CGImage) -> Int {
        let pixels = getPixelData(cgImage: cgImage)
        let w = cgImage.width
        var runLength = 0
        var firstColor = pixels[0] < 128

        for x in 0..<w {
            let idx = x * 4
            let isDark = idx < pixels.count && pixels[idx] < 128
            if isDark == firstColor {
                runLength += 1
            } else {
                break
            }
        }
        return max(21, w / max(1, runLength))
    }

    private func getPixelData(cgImage: CGImage) -> [UInt8] {
        let w = cgImage.width, h = cgImage.height
        var pixels = [UInt8](repeating: 0, count: w * h * 4)
        let colorSpace = CGColorSpaceCreateDeviceRGB()
        guard let ctx = CGContext(
            data: &pixels,
            width: w,
            height: h,
            bitsPerComponent: 8,
            bytesPerRow: w * 4,
            space: colorSpace,
            bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
        ) else { return pixels }
        ctx.draw(cgImage, in: CGRect(x: 0, y: 0, width: w, height: h))
        return pixels
    }

    private func averageColor(pixels: [UInt8]) -> (CGFloat, CGFloat, CGFloat) {
        var r: Double = 0, g: Double = 0, b: Double = 0
        let count = pixels.count / 4
        guard count > 0 else { return (0.5, 0.5, 0.5) }
        for i in stride(from: 0, to: pixels.count, by: 4) {
            r += Double(pixels[i])
            g += Double(pixels[i + 1])
            b += Double(pixels[i + 2])
        }
        let n = Double(count)
        return (CGFloat(r / n / 255), CGFloat(g / n / 255), CGFloat(b / n / 255))
    }
}
