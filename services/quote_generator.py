from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List
import json


class QuoteGenerator:
    """견적서 생성 서비스"""

    def __init__(self, output_dir: str = "static/quotes"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 한글 폰트 등록 (Windows 기본 폰트 사용)
        try:
            pdfmetrics.registerFont(TTFont('Malgun', 'malgun.ttf'))
            self.font_name = 'Malgun'
        except:
            # 폰트가 없으면 기본 폰트 사용 (한글 깨질 수 있음)
            self.font_name = 'Helvetica'

        self._load_product_data()

    def _load_product_data(self):
        """제품 데이터 로드"""
        products_path = Path(__file__).parent.parent / "data" / "products.json"
        with open(products_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.products = {p["id"]: p for p in data["products"]}
            self.installation_fee = data["installation_fee"]
            self.color_options = data["color_options"]

    def generate_quote(
        self,
        consultation_data: Dict,
        recommended_products: List[Dict],
        output_filename: str = None
    ) -> str:
        """
        견적서 PDF 생성

        Args:
            consultation_data: 상담 데이터
            recommended_products: 추천 제품 리스트
            output_filename: 출력 파일명

        Returns:
            생성된 PDF 파일 경로
        """
        if not output_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"quote_{timestamp}.pdf"

        output_path = self.output_dir / output_filename

        # PDF 문서 생성
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )

        # 스타일 설정
        styles = self._create_styles()

        # 문서 요소 리스트
        elements = []

        # 헤더
        elements.extend(self._create_header(styles))
        elements.append(Spacer(1, 0.5*cm))

        # 고객 정보
        elements.extend(self._create_customer_info(consultation_data, styles))
        elements.append(Spacer(1, 0.5*cm))

        # 제품 목록
        product_total = self._create_product_table(
            recommended_products,
            elements,
            styles,
            consultation_data.get("product_color", "wood")
        )
        elements.append(Spacer(1, 0.5*cm))

        # 금액 계산
        elements.extend(self._create_price_summary(
            product_total,
            consultation_data,
            styles
        ))
        elements.append(Spacer(1, 0.5*cm))

        # 설치 일정 안내
        elements.extend(self._create_installation_schedule(styles))
        elements.append(Spacer(1, 0.5*cm))

        # 푸터
        elements.extend(self._create_footer(styles))

        # PDF 빌드
        doc.build(elements)

        return str(output_path)

    def _create_styles(self) -> Dict:
        """스타일 생성"""
        styles = getSampleStyleSheet()

        # 제목 스타일
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontName=self.font_name,
            fontSize=24,
            textColor=colors.HexColor('#2C3E50'),
            alignment=TA_CENTER,
            spaceAfter=12
        )

        # 소제목 스타일
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontName=self.font_name,
            fontSize=14,
            textColor=colors.HexColor('#34495E'),
            spaceAfter=6
        )

        # 본문 스타일
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontName=self.font_name,
            fontSize=10,
            leading=14
        )

        return {
            'title': title_style,
            'heading': heading_style,
            'body': body_style,
            'normal': styles['Normal']
        }

    def _create_header(self, styles: Dict) -> List:
        """헤더 생성"""
        elements = []

        # 회사 로고 (있다면)
        # logo_path = Path("static/images/logo.png")
        # if logo_path.exists():
        #     logo = Image(str(logo_path), width=3*cm, height=3*cm)
        #     elements.append(logo)

        # 제목
        title = Paragraph("PLAYCAT 고양이 행동풍부화<br/>설치 견적서", styles['title'])
        elements.append(title)

        # 날짜
        date_text = f"견적일자: {datetime.now().strftime('%Y년 %m월 %d일')}"
        date_para = Paragraph(date_text, styles['body'])
        elements.append(date_para)

        return elements

    def _create_customer_info(self, data: Dict, styles: Dict) -> List:
        """고객 정보 섹션"""
        elements = []

        heading = Paragraph("상담 정보", styles['heading'])
        elements.append(heading)

        info_data = [
            ['설치 지역', data.get('installation_region', '-')],
            ['설치 장소', data.get('installation_location', '-')],
            ['고양이 수', f"{data.get('cat_count', 0)}마리"],
            ['공간 크기', f"가로 {data.get('width', 0)}cm × 세로 {data.get('height', 0)}cm × 높이 {data.get('ceiling_height', 0)}cm"],
            ['제품 컬러', self.color_options.get(data.get('product_color', 'wood'), {}).get('name', '-')]
        ]

        table = Table(info_data, colWidths=[4*cm, 12*cm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ECF0F1')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#2C3E50')),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))

        elements.append(table)
        return elements

    def _create_product_table(
        self,
        products: List[Dict],
        elements: List,
        styles: Dict,
        color_option: str
    ) -> float:
        """제품 목록 테이블 생성"""
        heading = Paragraph("제품 구성", styles['heading'])
        elements.append(heading)

        # 테이블 헤더
        table_data = [
            ['제품명', '규격', '수량', '단가', '금액']
        ]

        total = 0.0
        color_multiplier = self.color_options.get(color_option, {}).get('price_multiplier', 1.0)

        for product in products:
            product_id = product.get('id')
            quantity = product.get('quantity', 1)

            product_info = self.products.get(product_id)
            if not product_info:
                continue

            name = product_info['name']
            size = product_info['size']

            # 규격 문자열
            if 'diameter' in size:
                size_str = f"Ø{size['diameter']}cm"
            else:
                size_str = f"{size['width']}×{size['depth']}×{size['height']}cm"

            # 가격 계산
            unit_price = product_info['base_price'] * color_multiplier
            line_total = unit_price * quantity
            total += line_total

            table_data.append([
                name,
                size_str,
                f"{quantity}개",
                f"{int(unit_price):,}원",
                f"{int(line_total):,}원"
            ])

        # 테이블 생성
        table = Table(table_data, colWidths=[6*cm, 3*cm, 2*cm, 3*cm, 3*cm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTNAME', (0, 0), (-1, 0), self.font_name),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))

        elements.append(table)
        return total

    def _create_price_summary(
        self,
        product_total: float,
        data: Dict,
        styles: Dict
    ) -> List:
        """금액 요약"""
        elements = []

        heading = Paragraph("견적 금액", styles['heading'])
        elements.append(heading)

        # 지역별 할증 계산
        region = data.get('installation_region', '')
        regional_surcharge = 0

        for key, value in self.installation_fee['regional_surcharge'].items():
            if key in region:
                regional_surcharge = value
                break

        # 설치비
        product_count = sum(p.get('quantity', 1) for p in data.get('products', []))
        installation_fee = (
            self.installation_fee['base'] +
            self.installation_fee['per_product'] * product_count +
            regional_surcharge
        )

        # 총액
        total = product_total + installation_fee

        summary_data = [
            ['제품 금액', f"{int(product_total):,}원"],
            ['기본 설치비', f"{self.installation_fee['base']:,}원"],
            ['제품별 설치비', f"{self.installation_fee['per_product'] * product_count:,}원"],
            ['지역 할증', f"{regional_surcharge:,}원"],
            ['', ''],
            ['총 견적 금액', f"{int(total):,}원"]
        ]

        table = Table(summary_data, colWidths=[12*cm, 5*cm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.font_name),
            ('FONTSIZE', (0, 0), (-1, -2), 10),
            ('FONTSIZE', (0, -1), (-1, -1), 14),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -2), 0.5, colors.grey),
            ('LINEABOVE', (0, -1), (-1, -1), 2, colors.HexColor('#2C3E50')),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#ECF0F1')),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#E74C3C')),
            ('FONTNAME', (0, -1), (-1, -1), self.font_name),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))

        elements.append(table)
        return elements

    def _create_installation_schedule(self, styles: Dict) -> List:
        """설치 일정 안내"""
        elements = []

        heading = Paragraph("설치 가능 일정", styles['heading'])
        elements.append(heading)

        # 오늘 기준 가능한 날짜 (예: 2주 후부터)
        today = datetime.now()
        earliest_date = today + timedelta(days=14)

        schedule_text = f"""
        선결제(완불) 확인 후 제작에 들어가며, 제작 기간은 약 7-10일 소요됩니다.<br/>
        <br/>
        <b>최소 설치 가능일:</b> {earliest_date.strftime('%Y년 %m월 %d일')} 이후<br/>
        <br/>
        정확한 설치 일정은 결제 확인 후 개별 연락드립니다.<br/>
        이사 예정이신 경우 이사 후 가구 배치가 끝난 다음 설치를 권장드립니다.
        """

        para = Paragraph(schedule_text, styles['body'])
        elements.append(para)

        return elements

    def _create_footer(self, styles: Dict) -> List:
        """푸터"""
        elements = []

        elements.append(Spacer(1, 1*cm))

        footer_text = """
        <b>PLAYCAT - 플레이캣</b><br/>
        경기도 시흥시 연성로 156번길 39<br/>
        Tel: 1522-5092 / 010-5676-8282<br/>
        Email: thebloomkr@naver.com<br/>
        Web: www.playcat.kr<br/>
        Instagram: @playcat.kr<br/>
        <br/>
        본 견적서는 {validity}까지 유효합니다.<br/>
        견적 문의사항은 언제든지 연락 주시기 바랍니다.
        """.format(
            validity=(datetime.now() + timedelta(days=30)).strftime('%Y년 %m월 %d일')
        )

        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['body'],
            fontSize=8,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#7F8C8D')
        )

        para = Paragraph(footer_text, footer_style)
        elements.append(para)

        return elements


# 전역 인스턴스
quote_generator = QuoteGenerator()
