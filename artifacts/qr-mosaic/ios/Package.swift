// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "QRMosaic",
    platforms: [.iOS(.v15), .macOS(.v12)],
    products: [
        .library(name: "QRMosaic", targets: ["QRMosaic"]),
    ],
    targets: [
        .target(
            name: "QRMosaic",
            path: "Sources/QRMosaic"
        ),
        .testTarget(
            name: "QRMosaicTests",
            dependencies: ["QRMosaic"],
            path: "Tests/QRMosaicTests"
        ),
    ]
)
