// OGP画像（1200×630）を作る：実写写真 + ロゴ + キャッチコピー。macOS の Swift で動く。
// 使い方: swift tools/make_ogp.swift
//   → src/static/ogp.jpg を書き出す（SNSでURLを共有したときのサムネイル）
import AppKit
import CoreGraphics

let root = URL(fileURLWithPath: CommandLine.arguments[0]).deletingLastPathComponent().deletingLastPathComponent()
let photoURL = root.appendingPathComponent("src/static/assets/img/photos/12-studio-work.jpg")
let logoURL = root.appendingPathComponent("src/static/assets/img/renew-logo-black.png")
let outURL = root.appendingPathComponent("src/static/ogp.jpg")

let W = 1200, H = 630

func load(_ url: URL) -> CGImage {
    guard let src = CGImageSourceCreateWithURL(url as CFURL, nil), let img = CGImageSourceCreateImageAtIndex(src, 0, nil) else {
        fatalError("読み込めません: \(url.path)")
    }
    return img
}

let photo = load(photoURL)
let logo = load(logoURL)

let cs = CGColorSpaceCreateDeviceRGB()
let ctx = CGContext(data: nil, width: W, height: H, bitsPerComponent: 8, bytesPerRow: 0, space: cs,
                    bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue)!
ctx.interpolationQuality = .high

// 1) 写真：横幅いっぱいに拡大し、人物と車が入るよう縦位置を決めて切り抜く（CoreGraphicsは下が原点）
let scale = CGFloat(W) / CGFloat(photo.width)
let drawH = CGFloat(photo.height) * scale
let yOffset = -(drawH - CGFloat(H)) * 0.62  // 写真の上寄りを使い、人物の頭が切れないようにする
ctx.draw(photo, in: CGRect(x: 0, y: yOffset, width: CGFloat(W), height: drawH))

// 2) 暗いグラデーション（左・下を暗くして文字を読みやすくする）
let grad = CGGradient(colorsSpace: cs, colors: [
    CGColor(red: 0, green: 0, blue: 0, alpha: 0.78),
    CGColor(red: 0, green: 0, blue: 0, alpha: 0.35),
    CGColor(red: 0, green: 0, blue: 0, alpha: 0.0),
] as CFArray, locations: [0, 0.5, 1])!
ctx.drawLinearGradient(grad, start: CGPoint(x: 0, y: 0), end: CGPoint(x: CGFloat(W) * 0.75, y: 0), options: [])
let grad2 = CGGradient(colorsSpace: cs, colors: [
    CGColor(red: 0, green: 0, blue: 0, alpha: 0.7),
    CGColor(red: 0, green: 0, blue: 0, alpha: 0.0),
] as CFArray, locations: [0, 1])!
ctx.drawLinearGradient(grad2, start: CGPoint(x: 0, y: 0), end: CGPoint(x: 0, y: CGFloat(H) * 0.55), options: [])

// 3) ロゴ（黒いPNGの形を白で塗る）：左上
let logoW: CGFloat = 330
let logoH = logoW * CGFloat(logo.height) / CGFloat(logo.width)
let logoRect = CGRect(x: 72, y: CGFloat(H) - 72 - logoH, width: logoW, height: logoH)
ctx.saveGState()
ctx.clip(to: logoRect, mask: logo)
ctx.setFillColor(CGColor(red: 1, green: 1, blue: 1, alpha: 1))
ctx.fill(logoRect)
ctx.restoreGState()

// 4) 文字：キャッチコピーとサブコピー（左下）
func drawText(_ s: String, size: CGFloat, weight: String, kern: CGFloat, at p: CGPoint) {
    let font = NSFont(name: weight, size: size) ?? NSFont.systemFont(ofSize: size, weight: .semibold)
    let attrs: [NSAttributedString.Key: Any] = [.font: font, .foregroundColor: NSColor.white, .kern: kern]
    let line = CTLineCreateWithAttributedString(NSAttributedString(string: s, attributes: attrs))
    ctx.textPosition = p
    CTLineDraw(line, ctx)
}
drawText("新車よりも、綺麗に。", size: 64, weight: "HiraginoSans-W6", kern: 6, at: CGPoint(x: 72, y: 150))
drawText("SOUKI -創綺- 車の美容院　｜　岡山県和気町", size: 24, weight: "HiraginoSans-W3", kern: 3, at: CGPoint(x: 74, y: 92))

// 5) JPEGで書き出し
let out = ctx.makeImage()!
let rep = NSBitmapImageRep(cgImage: out)
guard let data = rep.representation(using: .jpeg, properties: [.compressionFactor: 0.86]) else { fatalError("JPEG化に失敗") }
try! data.write(to: outURL)
print("OGP画像を書き出しました: \(outURL.path) (\(data.count / 1024)KB)")
