// swift-tools-version: 5.9
// Auto Stabilize (autoyaw): fisheyeklippet in, Stab Yaw ut. Läser Darkroms hörnmärke med IgelkottLensMark och tar
// kamerans linsmodell ur _shared/IgelkottFisheyeLens. Bygg utanför Drive:
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
