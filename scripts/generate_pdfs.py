"""Tạo PDF tài liệu mẫu tiếng Việt cho RAG pipeline.

Nội dung dựa trên căn cứ pháp lý thật (không phải văn bản tự bịa):
- Bộ luật Lao động 2019 (Điều 113, 114) — nghỉ phép năm
- Luật Thương mại 2005 — hợp đồng mua bán hàng hóa
- Luật Bảo vệ quyền lợi người tiêu dùng 2023 (số 19/2023/QH15, hiệu lực 01/07/2024) — đổi trả, bảo hành

Dùng fitz.Story + DocumentWriter (không dùng insert_text) vì insert_text với
TTF font không sinh ToUnicode CMap đúng, khiến trích xuất text sau này ra
ký tự lỗi (·) dù hiển thị PDF vẫn đúng.
"""
from pathlib import Path

import fitz

OUT = Path(__file__).resolve().parent.parent / "data" / "documents"


def escape_html(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def write_pdf(filename: str, title: str, sections: list[tuple[str, str]]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    parts = [f"<h1>{escape_html(title)}</h1>"]
    for heading, body in sections:
        parts.append(f"<h2>{escape_html(heading)}</h2>")
        for line in body.split("\n"):
            parts.append(f"<p>{escape_html(line)}</p>")
    html = "<div>" + "".join(parts) + "</div>"
    css = "p { margin: 2px 0; } h1 { font-size: 18px; } h2 { font-size: 14px; margin-top: 10px; }"

    story = fitz.Story(html=html, user_css=css)
    out_path = OUT / filename
    writer = fitz.DocumentWriter(str(out_path))
    mediabox = fitz.paper_rect("a4")
    where = mediabox + (40, 40, -40, -40)
    more = 1
    while more:
        dev = writer.begin_page(mediabox)
        more, _ = story.place(where)
        story.draw(dev)
        writer.end_page()
    writer.close()


def main() -> None:
    write_pdf(
        "hop-dong-mau.pdf",
        "HỢP ĐỒNG MUA BÁN HÀNG HÓA",
        [
            (
                "Căn cứ pháp lý",
                "Bộ luật Dân sự 2015; Luật Thương mại 2005 (số 36/2005/QH11).\n"
                "Bên A (Bên bán): CÔNG TY CỔ PHẦN THƯƠNG MẠI CÔNG TY BÁN LẺ\n"
                "Bên B (Bên mua): Theo thông tin đăng ký trên đơn hàng.",
            ),
            (
                "Điều 1: Đối tượng hợp đồng",
                "Bên A cung cấp hàng hóa (sản phẩm điện tử, thực phẩm, gia dụng, văn phòng phẩm)\n"
                "theo báo giá và đơn đặt hàng được hai bên xác nhận bằng văn bản.",
            ),
            (
                "Điều 2: Số lượng, chất lượng",
                "Số lượng, quy cách, chất lượng hàng hóa được quy định chi tiết trong\n"
                "Phụ lục đơn hàng, phù hợp tiêu chuẩn công bố của nhà sản xuất.",
            ),
            (
                "Điều 3: Giá cả",
                "Giá hàng hóa đã bao gồm thuế GTGT, được niêm yết tại thời điểm đặt hàng.\n"
                "Giá không đổi trong thời hạn hiệu lực báo giá (30 ngày).",
            ),
            (
                "Điều 4: Giao hàng",
                "Bên A giao hàng trong vòng 5-10 ngày làm việc kể từ khi nhận được\n"
                "50% giá trị hợp đồng. Địa điểm giao hàng theo địa chỉ Bên B cung cấp.",
            ),
            (
                "Điều 5: Thanh toán",
                "Bên B thanh toán 50% giá trị hợp đồng trong vòng 7 ngày kể từ ngày ký.\n"
                "50% còn lại thanh toán trong vòng 30 ngày sau khi nghiệm thu, bàn giao.\n"
                "Phương thức: chuyển khoản ngân hàng hoặc tiền mặt, chi phí chuyển khoản\n"
                "do Bên B chịu (theo thông lệ hợp đồng mua bán hàng hóa - Luật Thương mại 2005).",
            ),
            (
                "Điều 6: Bảo hành",
                "Thời gian bảo hành là 12 tháng kể từ ngày bàn giao sản phẩm.\n"
                "Bảo hành không áp dụng cho hư hỏng do sử dụng sai cách, thiên tai, hoặc\n"
                "tự ý sửa chữa bởi bên thứ ba không được ủy quyền.",
            ),
            (
                "Điều 7: Trách nhiệm các bên",
                "Bên A chịu trách nhiệm về chất lượng hàng hóa đúng cam kết.\n"
                "Bên B chịu trách nhiệm thanh toán đúng hạn; chậm thanh toán quá 15 ngày\n"
                "chịu lãi suất chậm trả theo lãi suất nợ quá hạn của ngân hàng thương mại.",
            ),
            (
                "Điều 8: Giải quyết tranh chấp",
                "Mọi tranh chấp ưu tiên giải quyết qua thương lượng, hòa giải.\n"
                "Nếu không thành, tranh chấp được đưa ra Tòa án có thẩm quyền theo\n"
                "quy định pháp luật Việt Nam hiện hành.",
            ),
        ],
    )
    write_pdf(
        "faq-noi-bo.pdf",
        "FAQ NỘI BỘ NHÂN VIÊN",
        [
            (
                "Căn cứ pháp lý",
                "Bộ luật Lao động 2019 (số 45/2019/QH14), Điều 113, 114.",
            ),
            (
                "1. Nghỉ phép năm được bao nhiêu ngày?",
                "Nhân viên chính thức làm việc đủ 12 tháng được nghỉ 12 ngày làm việc/năm\n"
                "hưởng nguyên lương (Điều 113 BLLĐ 2019, điều kiện làm việc bình thường).\n"
                "Lao động làm công việc nặng nhọc, độc hại được nghỉ 14 ngày/năm.\n"
                "Cứ 5 năm thâm niên được cộng thêm 1 ngày phép (Điều 114 BLLĐ 2019).\n"
                "Làm việc chưa đủ 12 tháng: số ngày phép tính theo tỷ lệ tháng làm việc.",
            ),
            (
                "2. Thủ tục xin nghỉ phép",
                "Đơn xin nghỉ gửi trưởng phòng trực tiếp trước ít nhất 3 ngày làm việc.\n"
                "Nghỉ phép đột xuất (ốm đau, việc gia đình) báo trước ít nhất 4 giờ.",
            ),
            (
                "3. Quy trình đặt hàng nội bộ",
                "Đơn hàng trên 20 triệu đồng cần phê duyệt của trưởng phòng kinh doanh.\n"
                "Đơn hàng trên 50 triệu đồng cần phê duyệt của giám đốc kinh doanh.\n"
                "Đơn hàng trên 100 triệu đồng cần phê duyệt của Ban Giám đốc.",
            ),
            (
                "4. Làm thêm giờ",
                "Làm thêm giờ không quá 40 giờ/tháng và 200 giờ/năm (trường hợp đặc biệt\n"
                "tối đa 300 giờ/năm theo quy định pháp luật). Lương làm thêm tính tối thiểu\n"
                "150% ngày thường, 200% ngày nghỉ hàng tuần, 300% ngày lễ/tết.",
            ),
        ],
    )
    write_pdf(
        "chinh-sach-ban-hang.pdf",
        "CHÍNH SÁCH BÁN HÀNG",
        [
            (
                "Căn cứ pháp lý",
                "Luật Bảo vệ quyền lợi người tiêu dùng 2023 (số 19/2023/QH15,\n"
                "hiệu lực từ 01/07/2024); Luật Thương mại 2005.",
            ),
            (
                "1. Chính sách chiết khấu",
                "Đơn hàng từ 50 triệu đồng: chiết khấu 5%.\n"
                "Đơn hàng từ 80 triệu đồng: chiết khấu 8%.\n"
                "Đơn hàng từ 100 triệu đồng: chiết khấu 10%.\n"
                "Chiết khấu áp dụng trên giá trị trước thuế, không cộng dồn với khuyến mãi khác.",
            ),
            (
                "2. Chính sách đổi trả",
                "Sản phẩm lỗi kỹ thuật được đổi trong vòng 30 ngày kể từ ngày mua,\n"
                "sản phẩm còn nguyên vẹn, đầy đủ phụ kiện, hợp lệ và hóa đơn.\n"
                "Theo Luật Bảo vệ quyền lợi người tiêu dùng 2023: nếu đã bảo hành từ 3 lần\n"
                "trở lên trong thời hạn bảo hành mà không khắc phục được lỗi, bên bán phải\n"
                "đổi sản phẩm mới tương tự hoặc hoàn tiền cho khách hàng.",
            ),
            (
                "3. Bảo hành sau đổi trả",
                "Khi đổi sản phẩm mới, thời hạn bảo hành được tính lại từ thời điểm đổi.\n"
                "Thời gian bảo hành tiêu chuẩn: 12 tháng đối với hàng điện tử, 6 tháng\n"
                "đối với hàng gia dụng nhỏ.",
            ),
            (
                "4. Quyền lợi khách hàng",
                "Khách hàng được cung cấp hóa đơn, thông tin nguồn gốc sản phẩm đầy đủ.\n"
                "Mọi khiếu nại được tiếp nhận và phản hồi trong vòng 5 ngày làm việc.",
            ),
        ],
    )


if __name__ == "__main__":
    main()
