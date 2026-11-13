// Cut the person out of a photo (transparent background) with Apple Vision. macOS 12+ only.
// Usage: swift cutout.swift <in.png or .jpg> <out.png>
import Foundation
import Vision
import CoreImage
import CoreImage.CIFilterBuiltins
import ImageIO
import UniformTypeIdentifiers

let args = CommandLine.arguments
guard args.count == 3 else { print("usage: cutout <in> <out.png>"); exit(1) }
let input = CIImage(contentsOf: URL(fileURLWithPath: args[1]))!

let req = VNGeneratePersonSegmentationRequest()
req.qualityLevel = .accurate
req.outputPixelFormat = kCVPixelFormatType_OneComponent8
try VNImageRequestHandler(ciImage: input).perform([req])
guard let maskBuf = req.results?.first?.pixelBuffer else { print("no person found"); exit(2) }

var mask = CIImage(cvPixelBuffer: maskBuf)
mask = mask.transformed(by: CGAffineTransform(scaleX: input.extent.width / mask.extent.width,
                                              y: input.extent.height / mask.extent.height))
let blend = CIFilter.blendWithMask()
blend.inputImage = input
blend.backgroundImage = CIImage(color: .clear).cropped(to: input.extent)
blend.maskImage = mask
let ctx = CIContext()
let cg = ctx.createCGImage(blend.outputImage!, from: input.extent, format: .RGBA8, colorSpace: CGColorSpace(name: CGColorSpace.sRGB)!)!
let dest = CGImageDestinationCreateWithURL(URL(fileURLWithPath: args[2]) as CFURL, UTType.png.identifier as CFString, 1, nil)!
CGImageDestinationAddImage(dest, cg, nil)
CGImageDestinationFinalize(dest)
print("ok")
