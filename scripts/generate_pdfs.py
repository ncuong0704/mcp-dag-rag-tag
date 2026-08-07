"""Tạo PDF tài liệu mẫu tiếng Việt cho RAG pipeline."""
from pathlib import Path

import fitz

OUT = Path(__file__).resolve().parent.parent / "data" / "documents"
FONT_PATHS = [
    Path("C:/Windows/Fonts/arial.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
]


def get_fontfile() -> str | None:
    for path in FONT_PATHS:
        if path.exists():
            return str(path)
    return None


def write_pdf(filename: str, title: str, sections: list[tuple[str, str]]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fontfile = get_fontfile()
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    y = 50

    def write_line(text: str, size: float = 12, gap: float = 18) -> None:
        nonlocal y, page
        if y > 780:
            page = doc.new_page(width=595, height=842)
            y = 50
        kwargs: dict = {"fontsize": size}
        if fontfile:
            kwargs["fontfile"] = fontfile
        else:
            kwargs["fontname"] = "helv"
        page.insert_text((50, y), text, **kwargs)
        y += gap

    write_line(title, size=16, gap=28)
    for heading, body in sections:
        write_line(heading, size=13, gap=22)
        for line in body.split("\n"):
            write_line(line, size=11, gap=16)
        y += 8

    doc.save(str(OUT / filename))
    doc.close()


def main() -> None:
    write_pdf(
        "hop-dong-mau.pdf",
        "HỢP ĐỒNG CUNG CẤP DỊCH VỤ",
        [
            (
                "Điều 5: Thanh toán",
                "Bên B thanh toán 50% giá trị hợp đồng trong vòng 7 ngày kể từ ngày ký. "
                "50% còn lại thanh toán trong vòng 30 ngày sau nghiệm thu. "
                "Thanh toán bằng chuyển khoản ngân hàng hoặc tiền mặt.",
            ),
            (
                "Điều 6: Bảo hành",
                "Thời gian bảo hành là 12 tháng kể từ ngày bàn giao sản phẩm. "
                "Bảo hành không áp dụng cho hư hỏng do sử dụng sai cách.",
            ),
        ],
    )
    write_pdf(
        "faq-noi-bo.pdf",
        "FAQ NỘI BỘ NHÂN VIÊN",
        [
            (
                "Nghỉ phép",
                "Nhân viên chính thức được 12 ngày phép năm. "
                "Ngày phép tăng thêm 1 ngày sau mỗi 5 năm thâm niên. "
                "Đơn xin nghỉ gửi trước ít nhất 3 ngày làm việc.",
            ),
            (
                "Quy trình đặt hàng",
                "Đơn hàng trên 20 triệu cần phê duyệt trưởng phòng. "
                "Đơn hàng trên 50 triệu cần phê duyệt giám đốc kinh doanh.",
            ),
        ],
    )
    write_pdf(
        "chinh-sach-ban-hang.pdf",
        "CHÍNH SÁCH BÁN HÀNG",
        [
            (
                "Chiết khấu",
                "Đơn hàng từ 50 triệu: chiết khấu 5%. "
                "Đơn hàng từ 80 triệu: chiết khấu 8%. "
                "Đơn hàng từ 100 triệu: chiết khấu 10%. "
                "Chiết khấu áp dụng trên giá trị trước thuế.",
            ),
            (
                "Đổi trả",
                "Sản phẩm lỗi được đổi trong 30 ngày. "
                "Sản phẩm nguyên vẹn, còn đầy đủ phụ kiện và hóa đơn.",
            ),
        ],
    )


if __name__ == "__main__":
    main()
