#!/usr/bin/env python3
"""
Script to add the new comprehensive personal care and beauty products to the database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.postgres_handler import postgres_handler
import json

# New product data based on your business description
new_products = [
    {
        "id": "0d4bc440-ff0a-4d4e-a5e8-cf83578af78a",
        "name": "Lux Soft Touch Beauty Soap",
        "slug": "lux-soft-touch-beauty-soap",
        "description": "Premium beauty soap with French rose and almond oil. Luxurious fragrance and moisturizing formula for soft, smooth skin.",
        "price": 45.00,
        "sale_price": 40.00,
        "stock_count": 150,
        "image_url": "https://5.imimg.com/data5/SD/ER/NC/SELLER-38185761/lux-soft-touch-soap-500x500.png",
        "images": ["https://5.imimg.com/data5/SD/ER/NC/SELLER-38185761/lux-soft-touch-soap-500x500.png"],
        "rating": 4.50,
        "review_count": 342,
        "is_active": True,
        "category_id": "ce827965-230f-4622-b66c-17728beec8fb",
        "product_tag": ["premium soap", "moisturizing", "french rose", "almond oil", "luxury skincare", "beauty soap", "soft skin", "fragrant", "glycerin enriched", "daily use", "dermatologically tested", "gentle cleansing", "smooth skin", "spa experience", "natural ingredients", "skin nourishment", "feminine fragrance", "lux brand"]
    },
    {
        "id": "0de4bc53-c849-45b5-b7f2-58e8e3de8fb3",
        "name": "Garnier Fructis Strengthening Shampoo",
        "slug": "garnier-fructis-strengthening-shampoo",
        "description": "Fortifying shampoo with citrus protein and vitamin complex. Strengthens weak hair and prevents breakage.",
        "price": 295.00,
        "sale_price": None,
        "stock_count": 95,
        "image_url": "https://images-cdn.ubuy.co.in/661679daed112e49332f9a20-garnier-fructis-shampoo-for-all-hair.jpg",
        "images": ["https://images-cdn.ubuy.co.in/661679daed112e49332f9a20-garnier-fructis-shampoo-for-all-hair.jpg"],
        "rating": 4.20,
        "review_count": 203,
        "is_active": True,
        "category_id": "edd8304b-473c-4ac2-9bf9-5369b195596b",
        "product_tag": ["strengthening shampoo", "garnier fructis", "citrus protein", "vitamin complex", "weak hair treatment", "breakage prevention", "vitamin C", "amino acids", "hair fortification", "vitamin B3", "vitamin B6", "fragile hair care", "protective barrier", "fresh fragrance", "fine hair", "styling protection", "hair rebuilding", "energizing formula"]
    },
    {
        "id": "15a4e12e-fd88-4a9c-864c-ea2c4dbe22b2",
        "name": "Bajaj Almond Drops Hair Oil",
        "slug": "bajaj-almond-drops-hair-oil",
        "description": "Non-sticky almond hair oil with vitamin E. Light formula that nourishes hair without making it greasy.",
        "price": 145.00,
        "sale_price": None,
        "stock_count": 160,
        "image_url": "https://m.media-amazon.com/images/I/517p82ysXaL._UF1000,1000_QL80_.jpg",
        "images": ["https://m.media-amazon.com/images/I/517p82ysXaL._UF1000,1000_QL80_.jpg"],
        "rating": 4.40,
        "review_count": 534,
        "is_active": True,
        "category_id": "edd8304b-473c-4ac2-9bf9-5369b195596b",
        "product_tag": ["almond hair oil", "bajaj brand", "non-sticky formula", "vitamin E enriched", "lightweight oil", "sweet almond extract", "omega-3 fatty acids", "daily use oil", "frizz control", "natural shine", "fine hair suitable", "drop application", "quick absorption", "no greasy residue", "humid climate friendly", "styled hair compatible", "antioxidant protection", "hair elasticity"]
    },
    {
        "id": "16699403-4a24-4c8c-83f6-5d1a6b426212",
        "name": "AXE Dark Temptation Deodorant",
        "slug": "axe-dark-temptation-deodorant",
        "description": "Irresistible chocolate fragrance with 48-hour protection. Popular choice among young men in Bangladesh.",
        "price": 285.00,
        "sale_price": None,
        "stock_count": 140,
        "image_url": "https://i5.walmartimages.com/asr/af3de50a-1254-4b18-9f53-89e6fe03c354.0e7f08cb6d7756bdb6821d647ca7599c.jpeg",
        "images": ["https://i5.walmartimages.com/asr/af3de50a-1254-4b18-9f53-89e6fe03c354.0e7f08cb6d7756bdb6821d647ca7599c.jpeg"],
        "rating": 4.40,
        "review_count": 312,
        "is_active": True,
        "category_id": "989f2c88-5868-4074-8f7a-ff52f58a320a",
        "product_tag": ["axe dark temptation", "chocolate fragrance", "48-hour protection", "seductive scent", "dark chocolate vanilla amber", "dual action technology", "odor protection", "fragrance release", "young men favorite", "cult status", "bangladesh popular", "long-lasting formula", "modern grooming", "distinctive aroma", "premium fragrance", "magnetic appeal", "confidence booster", "sleek packaging", "style and substance"]
    },
    {
        "id": "17fd4a77-5a46-4896-8aaa-d158e9203002",
        "name": "Pantene Pro-V Silky Smooth Care Shampoo",
        "slug": "pantene-pro-v-silky-smooth-care-shampoo",
        "description": "Nourishing shampoo with Pro-Vitamin B5 and argan essence. Transforms rough, dull hair into silky smooth locks.",
        "price": 280.00,
        "sale_price": 265.00,
        "stock_count": 110,
        "image_url": "https://paikaree.com.bd/public/uploads/products/photos/pantene-pro-v-silky-smooth-care-shampoo---340ml-paikaree.webp",
        "images": ["https://paikaree.com.bd/public/uploads/products/photos/pantene-pro-v-silky-smooth-care-shampoo---340ml-paikaree.webp"],
        "rating": 4.40,
        "review_count": 312,
        "is_active": True,
        "category_id": "edd8304b-473c-4ac2-9bf9-5369b195596b",
        "product_tag": ["silky smooth shampoo", "pantene pro-v", "vitamin B5", "argan essence", "frizz control", "smooth hair", "hair transformation", "professional grade", "daily use shampoo", "chemically treated hair", "heat damage repair", "salon quality", "lightweight formula", "progressive smoothing", "shine enhancer", "manageable hair", "panthenol", "nourishing shampoo"]
    },
    {
        "id": "190d0a92-0aba-41ce-87db-96287bede2fe",
        "name": "Rasasi Attar Al Mohabbah",
        "slug": "rasasi-attar-al-mohabbah",
        "description": "Traditional Arabic attar with rose and oud notes. Alcohol-free concentrated perfume oil popular in Bangladesh.",
        "price": 650.00,
        "sale_price": 590.00,
        "stock_count": 45,
        "image_url": "https://images.unsplash.com/photo-1563170351-be82bc888aa4?w=500&h=500&fit=crop",
        "images": ["https://images.unsplash.com/photo-1563170351-be82bc888aa4?w=500&h=500&fit=crop"],
        "rating": 4.60,
        "review_count": 234,
        "is_active": True,
        "category_id": "989f2c88-5868-4074-8f7a-ff52f58a320a",
        "product_tag": ["rasasi attar", "al mohabbah", "arabic perfume", "rose oud blend", "alcohol-free", "concentrated oil", "damascus rose", "premium oud wood", "traditional perfumery", "middle eastern", "sensitive skin friendly", "long-lasting", "personalized scent", "bangladesh popular", "cultural significance", "heritage fragrance", "master perfumers", "authentic sophisticated", "exceptional value", "signature fragrance"]
    },
    {
        "id": "33546bae-eaf3-47ce-bfb0-ac4068506d4f",
        "name": "Sunsilk Hair Fall Solution Shampoo",
        "slug": "sunsilk-hair-fall-solution-shampoo",
        "description": "Anti-hair fall shampoo with keratin, argan oil and soy protein. Reduces hair fall by up to 98% and strengthens hair.",
        "price": 225.00,
        "sale_price": 210.00,
        "stock_count": 140,
        "image_url": "https://mygirlco.com/writable/uploads/filemanager/source/Unilever_Bangladesh/Unilever_October_SKU/2_Hairfallsolution.jpg",
        "images": ["https://mygirlco.com/writable/uploads/filemanager/source/Unilever_Bangladesh/Unilever_October_SKU/2_Hairfallsolution.jpg"],
        "rating": 4.50,
        "review_count": 421,
        "is_active": True,
        "category_id": "edd8304b-473c-4ac2-9bf9-5369b195596b",
        "product_tag": ["hair fall control", "keratin shampoo", "argan oil", "soy protein", "sunsilk", "anti-hair fall", "hair strengthening", "98% reduction", "clinical proven", "damaged hair repair", "hair growth", "breakage control", "vitamin E", "fatty acids", "gentle cleansing", "all hair types", "hair nourishment", "hair fall solution"]
    },
    {
        "id": "34b038b2-49c0-43fb-90d6-4ad9953f27c6",
        "name": "Keya Seth Neem Basil Face Wash",
        "slug": "keya-seth-neem-basil-face-wash",
        "description": "Herbal face wash with neem and basil extracts. Controls acne and purifies skin naturally. Made in Bangladesh.",
        "price": 180.00,
        "sale_price": 165.00,
        "stock_count": 80,
        "image_url": "https://www.keyaseth.com/cdn/shop/files/Neem_Tulsi_Pack_of_3.jpg?v=1751891386",
        "images": ["https://www.keyaseth.com/cdn/shop/files/Neem_Tulsi_Pack_of_3.jpg?v=1751891386"],
        "rating": 4.40,
        "review_count": 156,
        "is_active": True,
        "category_id": "7ca51b4e-42aa-4bc3-91e7-bb7ea6c9bf23",
        "product_tag": ["neem face wash", "basil extract", "keya seth", "herbal skincare", "acne control", "natural ingredients", "bangladeshi brand", "oil control", "pore cleanser", "antibacterial", "tulsi benefits", "ayurvedic skincare", "sulfate free", "paraben free", "oily skin", "combination skin", "traditional herbs", "pH balanced"]
    },
    {
        "id": "38ef231e-fd1b-4266-8e04-245047fe702f",
        "name": "Fair & Lovely Advanced Multi Vitamin Face Cream",
        "slug": "fair-lovely-advanced-multi-vitamin-face-cream",
        "description": "Advanced fairness cream with multivitamins and SPF protection. Popular whitening cream in Bangladesh.",
        "price": 195.00,
        "sale_price": 180.00,
        "stock_count": 175,
        "image_url": "https://jgsj.jayagrocer.com/cdn/shop/products/004022-1-1.jpg?v=1635035281",
        "images": ["https://jgsj.jayagrocer.com/cdn/shop/products/004022-1-1.jpg?v=1635035281"],
        "rating": 4.10,
        "review_count": 567,
        "is_active": True,
        "category_id": "7ca51b4e-42aa-4bc3-91e7-bb7ea6c9bf23",
        "product_tag": ["fair and lovely", "fairness cream", "multi vitamin complex", "spf protection", "skin brightening", "vitamin B3 C E", "antioxidant protection", "uv protection", "dark spot reduction", "even skin tone", "non-greasy formula", "daily use", "makeup base", "luminous complexion", "moisturizing", "dermatologically tested", "all skin types", "gentle formula", "radiant skin", "popular bangladesh"]
    },
    {
        "id": "43b95ad4-0fc0-4c04-ae77-7671696ca66a",
        "name": "Fogg Scent Xpressio Body Spray",
        "slug": "fogg-scent-xpressio-body-spray",
        "description": "Long-lasting body spray with fresh fragrance. No gas, only perfume - 800 sprays guaranteed.",
        "price": 245.00,
        "sale_price": 225.00,
        "stock_count": 120,
        "image_url": "https://bk.shajgoj.com/storage/2019/07/Fogg-Scent-Men-Xpressio-900.jpg",
        "images": ["https://bk.shajgoj.com/storage/2019/07/Fogg-Scent-Men-Xpressio-900.jpg"],
        "rating": 4.20,
        "review_count": 456,
        "is_active": True,
        "category_id": "989f2c88-5868-4074-8f7a-ff52f58a320a",
        "product_tag": ["fogg body spray", "no gas formula", "800 sprays", "pure perfume concentrate", "long-lasting fragrance", "xpressio scent", "citrus bergamot", "lavender geranium", "musk sandalwood", "pump mechanism", "alcohol based", "deodorizing action", "active lifestyle", "travel friendly", "skin gentle", "no staining", "innovative technology", "value for money", "all-day protection"]
    },
    {
        "id": "4ba24ba6-92f2-4393-872a-a1b810fad9aa",
        "name": "Herbal Essences Bio Coconut Milk Shampoo",
        "slug": "herbal-essences-bio-coconut-milk-shampoo",
        "description": "Organic coconut milk shampoo with white jasmine extracts. Deeply nourishes and hydrates dry, damaged hair.",
        "price": 385.00,
        "sale_price": 360.00,
        "stock_count": 75,
        "image_url": "https://m.media-amazon.com/images/I/81SeXH2U8hL._UF894,1000_QL80_.jpg",
        "images": ["https://m.media-amazon.com/images/I/81SeXH2U8hL._UF894,1000_QL80_.jpg"],
        "rating": 4.30,
        "review_count": 189,
        "is_active": True,
        "category_id": "edd8304b-473c-4ac2-9bf9-5369b195596b",
        "product_tag": ["organic coconut milk", "herbal essences", "white jasmine", "bio certified", "dry hair treatment", "damaged hair repair", "sulfate free", "paraben free", "natural proteins", "tropical hair care", "eco-friendly", "color safe", "sensitive scalp", "antioxidant protection", "lauric acid", "intensive nourishment", "luxury shampoo", "environmentally conscious"]
    },
    {
        "id": "55d26d11-22c2-4632-8d4b-10d8ced93269",
        "name": "Dove Beauty Bar Moisturizing Soap",
        "slug": "dove-beauty-bar-moisturizing-soap",
        "description": "Gentle cleansing bar with 1/4 moisturizing cream. Suitable for sensitive skin and provides deep nourishment.",
        "price": 65.00,
        "sale_price": 58.00,
        "stock_count": 120,
        "image_url": "https://i5.walmartimages.com/seo/Dove-Beauty-Bar-Women-s-Bath-Soap-Original-Deep-Moisturizing-All-Skin-3-75-oz-4-Bars_6c3c57b2-6438-4fec-85f1-8d06dbed434f.efc611ad9ca96683fa8a845b448c3c82.jpeg",
        "images": ["https://i5.walmartimages.com/seo/Dove-Beauty-Bar-Women-s-Bath-Soap-Original-Deep-Moisturizing-All-Skin-3-75-oz-4-Bars_6c3c57b2-6438-4fec-85f1-8d06dbed434f.efc611ad9ca96683fa8a845b448c3c82.jpeg"],
        "rating": 4.60,
        "review_count": 198,
        "is_active": True,
        "category_id": "ce827965-230f-4622-b66c-17728beec8fb",
        "product_tag": ["moisturizing soap", "beauty bar", "sensitive skin", "dove", "1/4 cream", "gentle cleansing", "dermatologist recommended", "non-comedogenic", "glycerin rich", "eczema friendly", "mild formula", "skin nourishment", "moisture barrier", "hypoallergenic", "creamy lather", "daily moisturizer", "soft skin", "clinical proven"]
    },
    {
        "id": "78cda270-cd24-45c8-b8d0-6e09ab3b54e9",
        "name": "Parachute Coconut Hair Oil",
        "slug": "parachute-coconut-hair-oil",
        "description": "Pure coconut oil for hair nourishment. Traditional formula that strengthens hair roots and promotes healthy growth.",
        "price": 165.00,
        "sale_price": 150.00,
        "stock_count": 180,
        "image_url": "https://bk.shajgoj.com/storage/2019/09/Parachute-Hair-Oil-Advansed-Enriched-Coconut-275ml-1.png",
        "images": ["https://bk.shajgoj.com/storage/2019/09/Parachute-Hair-Oil-Advansed-Enriched-Coconut-275ml-1.png"],
        "rating": 4.70,
        "review_count": 892,
        "is_active": True,
        "category_id": "edd8304b-473c-4ac2-9bf9-5369b195596b",
        "product_tag": ["pure coconut oil", "parachute brand", "traditional formula", "hair growth", "root strengthening", "vitamin E", "lauric acid", "capric acid", "protein loss prevention", "scalp massage", "antimicrobial", "dandruff prevention", "natural oil", "non-greasy", "pre-wash treatment", "overnight mask", "daily styling", "40 years trusted", "indian brand"]
    },
    {
        "id": "b5d6314d-b67d-4b6e-bd07-daee294f8588",
        "name": "Dabur Amla Hair Oil",
        "slug": "dabur-amla-hair-oil",
        "description": "Enriched with amla extracts and minerals. Prevents premature graying and strengthens hair from roots.",
        "price": 125.00,
        "sale_price": 115.00,
        "stock_count": 200,
        "image_url": "https://static-01.daraz.com.bd/p/89390a840b39268a365a9f3352ea5277.jpg",
        "images": ["https://static-01.daraz.com.bd/p/89390a840b39268a365a9f3352ea5277.jpg"],
        "rating": 4.50,
        "review_count": 678,
        "is_active": True,
        "category_id": "edd8304b-473c-4ac2-9bf9-5369b195596b",
        "product_tag": ["amla hair oil", "dabur ayurvedic", "premature graying prevention", "vitamin C rich", "natural melanin support", "antioxidant oil", "traditional extraction", "root strengthening", "essential minerals", "iron calcium phosphorus", "ayurvedic formula", "natural conditioning", "split end prevention", "hair texture improvement", "color preservation", "generational trust", "oxidative stress protection", "indian gooseberry"]
    },
    {
        "id": "b9f4f5cd-92de-4ab0-8c8e-745682c82b37",
        "name": "Wild Stone Code Platinum Perfume",
        "slug": "wild-stone-code-platinum-perfume",
        "description": "Premium long-lasting perfume with masculine woody notes. Sophisticated fragrance for special occasions.",
        "price": 485.00,
        "sale_price": 450.00,
        "stock_count": 85,
        "image_url": "https://codegrooming.com/cdn/shop/files/Platinum_c369f7b9-b1dd-42f0-bcbe-39d347e1ae5d.png?v=1713529441",
        "images": ["https://codegrooming.com/cdn/shop/files/Platinum_c369f7b9-b1dd-42f0-bcbe-39d347e1ae5d.png?v=1713529441"],
        "rating": 4.50,
        "review_count": 189,
        "is_active": True,
        "category_id": "989f2c88-5868-4074-8f7a-ff52f58a320a",
        "product_tag": ["wild stone code platinum", "premium perfume", "masculine woody", "sophisticated fragrance", "special occasions", "bergamot apple", "geranium sage marine", "sandalwood cedarwood musk", "long-lasting formula", "complex composition", "unforgettable impression", "projection longevity", "accessible luxury", "elegant bottle", "evening events", "romantic fragrance", "refined taste", "masterfully crafted", "masculine elegance"]
    },
    {
        "id": "c84f8cfa-17bc-42ee-b268-1213ad1c84a8",
        "name": "Tibbet Sandal Turmeric Soap",
        "slug": "tibbet-sandal-turmeric-soap",
        "description": "Traditional ayurvedic soap with sandalwood and turmeric. Natural skin brightening and anti-bacterial properties.",
        "price": 55.00,
        "sale_price": None,
        "stock_count": 95,
        "image_url": "https://i.chaldn.com/_mpimage/tibet-luxury-pink-soap-natural-glow-100-gm?src=https%3A%2F%2Feggyolk.chaldal.com%2Fapi%2FPicture%2FRaw%3FpictureId%3D136211&q=best&v=1",
        "images": ["https://i.chaldn.com/_mpimage/tibet-luxury-pink-soap-natural-glow-100-gm?src=https%3A%2F%2Feggyolk.chaldal.com%2Fapi%2FPicture%2FRaw%3FpictureId%3D136211&q=best&v=1"],
        "rating": 4.20,
        "review_count": 124,
        "is_active": True,
        "category_id": "ce827965-230f-4622-b66c-17728beec8fb",
        "product_tag": ["sandalwood soap", "turmeric soap", "ayurvedic skincare", "natural brightening", "skin glow", "traditional recipe", "handcrafted soap", "anti-inflammatory", "curcumin benefits", "dark spot reduction", "even skin tone", "antimicrobial", "aromatherapy", "chemical free", "herbal soap", "golden glow", "ancient wisdom", "organic ingredients"]
    },
    {
        "id": "ea4f53c6-6c24-4869-ac9a-af3510a6f7fb",
        "name": "Keya Seth Joba Hair Oil",
        "slug": "keya-seth-joba-hair-oil",
        "description": "Herbal hair oil with hibiscus and joba extracts. Local Bangladeshi brand promoting natural hair care.",
        "price": 220.00,
        "sale_price": None,
        "stock_count": 65,
        "image_url": "https://www.keyaseth.com/cdn/shop/products/alopex-long-n-strong-hair-oil-reduces-hair-fall-promotes-hair-growth-nourishes-hair-follicles-no-mineral-oil-synthetics-fragrance-29678616805536.jpg?v=1727440179&width=600",
        "images": ["https://www.keyaseth.com/cdn/shop/products/alopex-long-n-strong-hair-oil-reduces-hair-fall-promotes-hair-growth-nourishes-hair-follicles-no-mineral-oil-synthetics-fragrance-29678616805536.jpg?v=1727440179&width=600"],
        "rating": 4.30,
        "review_count": 167,
        "is_active": True,
        "category_id": "edd8304b-473c-4ac2-9bf9-5369b195596b",
        "product_tag": ["hibiscus hair oil", "joba extract", "keya seth", "bangladeshi brand", "traditional bengali", "amino acids", "vitamin C", "alpha hydroxy acids", "hair growth stimulation", "scalp pH balance", "bhringraj", "fenugreek", "south asian botanicals", "chemical free", "sulfate free", "paraben free", "cold press extraction", "local communities", "authentic formulation", "bengali beauty secrets", "natural conditioning", "hair follicle strengthening"]
    },
    {
        "id": "ec00e983-e85f-4202-a732-a3c61955091c",
        "name": "Himalaya Purifying Neem Face Wash",
        "slug": "himalaya-purifying-neem-face-wash",
        "description": "Herbal face wash with neem and turmeric. Removes impurities and prevents pimples naturally.",
        "price": 135.00,
        "sale_price": None,
        "stock_count": 144,
        "image_url": "https://img.thecdn.in/301417/1683557811163_SKU-0591_1.jpg?width=600&format=webp",
        "images": ["https://img.thecdn.in/301417/1683557811163_SKU-0591_1.jpg?width=600&format=webp"],
        "rating": 4.30,
        "review_count": 398,
        "is_active": True,
        "category_id": "7ca51b4e-42aa-4bc3-91e7-bb7ea6c9bf23",
        "product_tag": ["himalaya neem", "purifying face wash", "herbal cleanser", "antibacterial neem", "turmeric benefits", "acne prevention", "ayurvedic skincare", "nimbidin nimbin", "anti-inflammatory", "antiseptic", "soap-free formula", "pH balanced", "deep cleansing", "sensitive skin safe", "daily use", "traditional ingredients", "chemical-free", "breakout control", "natural purification", "healthy skin"]
    },
    {
        "id": "eea137cc-8256-4c8a-bd43-6b4e32f4a727",
        "name": "Head & Shoulders Anti-Dandruff Shampoo",
        "slug": "head-shoulders-anti-dandruff-shampoo",
        "description": "Clinically proven anti-dandruff shampoo with zinc pyrithione. Removes dandruff and prevents recurrence.",
        "price": 320.00,
        "sale_price": None,
        "stock_count": 85,
        "image_url": "https://i5.walmartimages.com/seo/Head-and-Shoulders-Classic-Clean-Shampoo-Anti-Dandruff-32-1-fl-oz_93707dbe-3131-4b0d-b76c-da7eb8527710.733cc5d0309678908b4e0031c144055d.jpeg",
        "images": ["https://i5.walmartimages.com/seo/Head-and-Shoulders-Classic-Clean-Shampoo-Anti-Dandruff-32-1-fl-oz_93707dbe-3131-4b0d-b76c-da7eb8527710.733cc5d0309678908b4e0031c144055d.jpeg"],
        "rating": 4.60,
        "review_count": 267,
        "is_active": True,
        "category_id": "edd8304b-473c-4ac2-9bf9-5369b195596b",
        "product_tag": ["anti-dandruff shampoo", "zinc pyrithione", "head and shoulders", "dandruff removal", "scalp treatment", "flake free", "dermatologist recommended", "clinically proven", "malassezia control", "itch relief", "daily use", "color safe", "scalp health", "long-lasting protection", "gentle formula", "50 years trusted", "prevention", "medical grade"]
    },
    {
        "id": "f393674f-3c1d-4833-affb-2dec5e0e4ac6",
        "name": "Lifebuoy Total 10 Antibacterial Soap",
        "slug": "lifebuoy-total-10-antibacterial-soap",
        "description": "Advanced antibacterial protection soap with ActivNaturol Ingredient. Proven to remove 99.9% germs and provide 10x better protection.",
        "price": 35.00,
        "sale_price": None,
        "stock_count": 200,
        "image_url": "https://images-cdn.ubuy.ae/6417e15d910a176dbe1875dd-lifebuoy-with-active-silver-formula-soap.jpg",
        "images": ["https://images-cdn.ubuy.ae/6417e15d910a176dbe1875dd-lifebuoy-with-active-silver-formula-soap.jpg"],
        "rating": 4.30,
        "review_count": 287,
        "is_active": True,
        "category_id": "ce827965-230f-4622-b66c-17728beec8fb",
        "product_tag": ["antibacterial soap", "germ protection", "activnaturol", "lifebuoy", "health soap", "99.9% germ removal", "family protection", "hygiene", "daily use", "clinical grade", "bacteria fighter", "virus protection", "thyme oil", "pine oil", "protective barrier", "long-lasting freshness", "mild formulation", "disease prevention"]
    }
]

def add_products_to_database():
    """Add the new comprehensive beauty and personal care products to the database"""
    
    print("🚀 Adding comprehensive beauty and personal care products to database...")
    print(f"📦 Total products to add: {len(new_products)}")
    
    try:
        # Clear existing products first (optional - remove this if you want to keep old products)
        print("🧹 Clearing existing products...")
        postgres_handler.execute_command("DELETE FROM products WHERE 1=1")
        
        added_count = 0
        for product in new_products:
            try:
                # Insert product
                query = """
                INSERT INTO products (
                    id, name, slug, description, price, sale_price, stock_count,
                    image_url, images, rating, review_count, is_active,
                    category_id, created_at, updated_at, product_tag
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                    NOW(), NOW(), %s
                )
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    price = EXCLUDED.price,
                    sale_price = EXCLUDED.sale_price,
                    stock_count = EXCLUDED.stock_count,
                    product_tag = EXCLUDED.product_tag,
                    updated_at = NOW()
                """
                
                values = (
                    product['id'],
                    product['name'],
                    product['slug'],
                    product['description'],
                    product['price'],
                    product['sale_price'],
                    product['stock_count'],
                    product['image_url'],
                    product['images'],  # Pass as Python list, not JSON string
                    product['rating'],
                    product['review_count'],
                    product['is_active'],
                    product['category_id'],
                    product['product_tag']  # Pass as Python list, not JSON string
                )
                
                postgres_handler.execute_command(query, values)
                added_count += 1
                print(f"✅ Added: {product['name']}")
                
            except Exception as e:
                print(f"❌ Error adding {product['name']}: {e}")
                continue
        
        print(f"\n🎉 Successfully added {added_count}/{len(new_products)} products!")
        
        # Verify the addition
        total_products = postgres_handler.execute_query("SELECT COUNT(*) as count FROM products")[0]['count']
        print(f"📊 Total products in database: {total_products}")
        
        # Show some sample products
        print("\n📋 Sample products added:")
        sample_products = postgres_handler.execute_query(
            "SELECT name, price, array_length(product_tag, 1) as tag_count FROM products LIMIT 5"
        )
        for product in sample_products:
            print(f"  • {product['name']} - ₹{product['price']} ({product['tag_count']} tags)")
            
    except Exception as e:
        print(f"❌ Error in database operation: {e}")

if __name__ == "__main__":
    add_products_to_database()
