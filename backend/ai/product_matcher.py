"""
Product Matcher Module for UnidBox Order Copilot

This module matches parsed product intents to actual products in the catalog
using fuzzy matching, brand detection, and category filtering.
"""

import json
import os
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from difflib import SequenceMatcher


@dataclass
class MatchedProduct:
    """Represents a product matched from the catalog"""
    product_id: str
    name: str
    clean_name: str
    price: float
    original_price: Optional[float]
    brand: Optional[str]
    category: Optional[str]
    url: str
    image_path: Optional[str]
    match_score: float  # 0-1 confidence of match
    match_reason: str   # Why this product was matched


@dataclass
class MatchResult:
    """Result of matching a product intent to catalog"""
    query: str
    matches: List[MatchedProduct]
    best_match: Optional[MatchedProduct]
    total_found: int
    search_time_ms: float


class ProductMatcher:
    """
    Matches product queries to the UnidBox product catalog.
    
    Uses fuzzy string matching, brand detection, and category filtering
    to find the best matching products for dealer inquiries.
    """
    
    # Known brands in the catalog
    KNOWN_BRANDS = {
        "acorn": "Acorn",
        "spin": "Spin",
        "fanco": "Fanco",
        "crestar": "Crestar",
        "alaska": "Alaska",
        "tecno": "Tecno",
        "ef": "EF",
        "ka": "KA",
        "pozzi": "Pozzi",
        "worx": "WORX",
        "makita": "Makita",
    }
    
    # Category keywords
    CATEGORY_KEYWORDS = {
        "Ceiling Fans": ["ceiling fan", "fan", "dc fan", "wifi fan"],
        "Range Hoods": ["hood", "chimney", "range hood", "kitchen hood"],
        "Hobs & Stoves": ["hob", "stove", "cooktop", "gas hob", "induction"],
        "Kitchen Taps": ["kitchen tap", "sink tap", "faucet"],
        "Basin Taps": ["basin tap", "bathroom tap", "basin mixer"],
        "Power Tools": ["drill", "power tool", "grinder", "saw", "washer", "blower"],
        "Kitchen Sinks": ["sink", "kitchen sink"],
        "Bathroom Fixtures": ["bathroom", "shower", "toilet"],
        "Water Heaters": ["water heater", "heater"],
    }
    
    def __init__(self, catalog_path: Optional[str] = None):
        """
        Initialize the ProductMatcher with a product catalog.
        
        Args:
            catalog_path: Path to the JSON product catalog file
        """
        self.catalog: List[Dict[str, Any]] = []
        self.catalog_path = catalog_path
        
        if catalog_path:
            self.load_catalog(catalog_path)
    
    def load_catalog(self, path: str) -> None:
        """Load the product catalog from a JSON file"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                self.catalog = json.load(f)
            print(f"Loaded {len(self.catalog)} products from catalog")
        except Exception as e:
            print(f"Error loading catalog: {e}")
            self.catalog = []
    
    def load_catalog_from_data(self, products: List[Dict[str, Any]]) -> None:
        """Load the product catalog from a list of product dictionaries"""
        self.catalog = products
    
    def match(
        self,
        query: str,
        brand: Optional[str] = None,
        category: Optional[str] = None,
        max_results: int = 5,
        min_score: float = 0.3
    ) -> MatchResult:
        """
        Match a query to products in the catalog.
        
        Args:
            query: Search query (product name, description, etc.)
            brand: Optional brand filter
            category: Optional category filter
            max_results: Maximum number of results to return
            min_score: Minimum match score (0-1)
            
        Returns:
            MatchResult with matched products
        """
        import time
        start_time = time.time()
        
        if not self.catalog:
            return MatchResult(
                query=query,
                matches=[],
                best_match=None,
                total_found=0,
                search_time_ms=0
            )
        
        # Normalize query
        query_lower = query.lower().strip()
        
        # Detect brand from query if not provided
        detected_brand = brand
        if not detected_brand:
            for brand_key, brand_name in self.KNOWN_BRANDS.items():
                if brand_key in query_lower:
                    detected_brand = brand_name
                    break
        
        # Detect category from query if not provided
        detected_category = category
        if not detected_category:
            for cat_name, keywords in self.CATEGORY_KEYWORDS.items():
                if any(kw in query_lower for kw in keywords):
                    detected_category = cat_name
                    break
        
        # Score all products
        scored_products: List[Tuple[float, Dict[str, Any], str]] = []
        
        for product in self.catalog:
            score, reason = self._score_product(
                product, query_lower, detected_brand, detected_category
            )
            if score >= min_score:
                scored_products.append((score, product, reason))
        
        # Sort by score descending
        scored_products.sort(key=lambda x: x[0], reverse=True)
        
        # Convert to MatchedProduct objects
        matches = []
        for score, product, reason in scored_products[:max_results]:
            matches.append(self._to_matched_product(product, score, reason))
        
        end_time = time.time()
        search_time_ms = (end_time - start_time) * 1000
        
        return MatchResult(
            query=query,
            matches=matches,
            best_match=matches[0] if matches else None,
            total_found=len(scored_products),
            search_time_ms=search_time_ms
        )
    
    def match_multiple(
        self,
        queries: List[Dict[str, Any]],
        max_results_per_query: int = 3
    ) -> List[MatchResult]:
        """
        Match multiple product queries at once.
        
        Args:
            queries: List of query dicts with 'query', 'brand', 'category' keys
            max_results_per_query: Max results per query
            
        Returns:
            List of MatchResult objects
        """
        results = []
        for q in queries:
            result = self.match(
                query=q.get('query', ''),
                brand=q.get('brand'),
                category=q.get('category'),
                max_results=max_results_per_query
            )
            results.append(result)
        return results
    
    def get_by_category(self, category: str, limit: int = 20) -> List[MatchedProduct]:
        """Get products by category"""
        matches = []
        for product in self.catalog:
            product_name = product.get('name', '').lower()
            
            # Check if product matches category keywords
            keywords = self.CATEGORY_KEYWORDS.get(category, [])
            if any(kw in product_name for kw in keywords):
                matches.append(self._to_matched_product(product, 1.0, f"Category: {category}"))
        
        return matches[:limit]
    
    def get_by_brand(self, brand: str, limit: int = 20) -> List[MatchedProduct]:
        """Get products by brand"""
        brand_lower = brand.lower()
        matches = []
        
        for product in self.catalog:
            product_name = product.get('name', '').lower()
            if brand_lower in product_name:
                matches.append(self._to_matched_product(product, 1.0, f"Brand: {brand}"))
        
        return matches[:limit]
    
    def get_product_by_id(self, product_id: str) -> Optional[MatchedProduct]:
        """Get a specific product by ID"""
        for product in self.catalog:
            if product.get('item_id') == product_id:
                return self._to_matched_product(product, 1.0, "Exact ID match")
        return None
    
    def _score_product(
        self,
        product: Dict[str, Any],
        query: str,
        brand: Optional[str],
        category: Optional[str]
    ) -> Tuple[float, str]:
        """
        Score how well a product matches the query.
        
        Returns:
            Tuple of (score, reason)
        """
        product_name = product.get('name', '').lower()
        clean_name = product.get('clean_name', product_name).lower()
        
        score = 0.0
        reasons = []
        
        # Fuzzy match on name
        name_score = SequenceMatcher(None, query, clean_name).ratio()
        if name_score > 0.3:
            score += name_score * 0.5
            reasons.append(f"Name match: {name_score:.2f}")
        
        # Check for exact word matches
        query_words = set(query.split())
        name_words = set(clean_name.split())
        common_words = query_words & name_words
        if common_words:
            word_score = len(common_words) / max(len(query_words), 1)
            score += word_score * 0.3
            reasons.append(f"Word match: {len(common_words)} words")
        
        # Brand match bonus
        if brand:
            brand_lower = brand.lower()
            if brand_lower in product_name:
                score += 0.3
                reasons.append(f"Brand match: {brand}")
        
        # Category match bonus
        if category:
            keywords = self.CATEGORY_KEYWORDS.get(category, [])
            if any(kw in product_name for kw in keywords):
                score += 0.2
                reasons.append(f"Category match: {category}")
        
        # Cap score at 1.0
        score = min(score, 1.0)
        
        return score, "; ".join(reasons) if reasons else "No strong match"
    
    def _to_matched_product(
        self,
        product: Dict[str, Any],
        score: float,
        reason: str
    ) -> MatchedProduct:
        """Convert a catalog product to a MatchedProduct"""
        # Extract brand from name
        brand = None
        name_lower = product.get('name', '').lower()
        for brand_key, brand_name in self.KNOWN_BRANDS.items():
            if brand_key in name_lower:
                brand = brand_name
                break
        
        # Extract category
        category = None
        for cat_name, keywords in self.CATEGORY_KEYWORDS.items():
            if any(kw in name_lower for kw in keywords):
                category = cat_name
                break
        
        # Parse price
        price = product.get('price_numeric', 0)
        if not price:
            price_str = product.get('price', '0')
            price = float(re.sub(r'[^\d.]', '', price_str) or 0)
        
        original_price = None
        if product.get('original_price'):
            original_price = float(re.sub(r'[^\d.]', '', product['original_price']) or 0)
        
        return MatchedProduct(
            product_id=product.get('item_id', ''),
            name=product.get('name', ''),
            clean_name=product.get('clean_name', product.get('name', '')),
            price=price,
            original_price=original_price,
            brand=brand,
            category=category,
            url=product.get('url', ''),
            image_path=product.get('image_path'),
            match_score=score,
            match_reason=reason
        )
    
    def to_dict(self, result: MatchResult) -> Dict[str, Any]:
        """Convert MatchResult to dictionary for JSON serialization"""
        return {
            "query": result.query,
            "matches": [
                {
                    "product_id": m.product_id,
                    "name": m.name,
                    "clean_name": m.clean_name,
                    "price": m.price,
                    "original_price": m.original_price,
                    "brand": m.brand,
                    "category": m.category,
                    "url": m.url,
                    "image_path": m.image_path,
                    "match_score": m.match_score,
                    "match_reason": m.match_reason
                }
                for m in result.matches
            ],
            "best_match": {
                "product_id": result.best_match.product_id,
                "name": result.best_match.name,
                "price": result.best_match.price
            } if result.best_match else None,
            "total_found": result.total_found,
            "search_time_ms": result.search_time_ms
        }
