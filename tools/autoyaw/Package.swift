// swift-tools-version: 5.9
// Auto Stabilize (autoyaw): fisheye clip in, Stab Yaw out. Reads Darkroom's corner mark with IgelkottLensMark and takes
// the camera's lens model from _shared/IgelkottFisheyeLens. Build outside Drive:
//   swift build -c release --package-path tools/autoyaw --build-path ~/Library/Caches/Igelkott/IgelkottLiveFXFisheye/autoyaw-build
import PackageDescription

let package = Package(
    name: "autoyaw",
    platforms: [.macOS(.v14)],
    dependencies: [.package(path: "../../../_shared/IgelkottFisheyeLens")],
    targets: [
        .executableTarget(name: "autoyaw",
                          dependencies: [.product(name: "IgelkottFisheyeLens", package: "IgelkottFisheyeLens"),
                                         .product(name: "IgelkottLensMark", package: "IgelkottFisheyeLens")],
                          path: "Sources")
    ]
)
