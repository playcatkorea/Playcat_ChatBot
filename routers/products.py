"""
Products API Router
제품 정보 관련 엔드포인트 모듈
"""
from fastapi import APIRouter, HTTPException
from pathlib import Path
import json

# Router 생성
router = APIRouter(prefix="/api/products", tags=["products"])

# 제품 데이터 경로
PRODUCTS_FILE = Path("data/products.json")


@router.get("")
async def get_products():
    """
    전체 제품 목록 조회
    
    - 플레이캣 제품 카탈로그 반환
    - 캣타워, 캣워커, 액세서리 등
    """
    try:
        if not PRODUCTS_FILE.exists():
            raise HTTPException(status_code=404, detail="Products data not found")
        
        with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
            products = json.load(f)
        
        return {"products": products}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading products: {str(e)}")


@router.get("/{product_id}")
async def get_product_by_id(product_id: str):
    """특정 제품 정보 조회"""
    try:
        if not PRODUCTS_FILE.exists():
            raise HTTPException(status_code=404, detail="Products data not found")
        
        with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
            products = json.load(f)
        
        # 제품 검색
        product = next(
            (p for p in products if p.get("id") == product_id),
            None
        )
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return {"product": product}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/category/{category}")
async def get_products_by_category(category: str):
    """카테고리별 제품 조회"""
    try:
        if not PRODUCTS_FILE.exists():
            raise HTTPException(status_code=404, detail="Products data not found")
        
        with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
            products = json.load(f)
        
        # 카테고리 필터링
        filtered_products = [
            p for p in products
            if p.get("category", "").lower() == category.lower()
        ]
        
        return {
            "category": category,
            "count": len(filtered_products),
            "products": filtered_products
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
