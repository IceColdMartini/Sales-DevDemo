
CREATE TABLE products (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    price NUMERIC(10, 2) NOT NULL,
    sale_price NUMERIC(10, 2),
    stock_count INTEGER DEFAULT 0,
    image_url VARCHAR(255),
    images TEXT[],
    rating NUMERIC(3, 2) DEFAULT 0,
    review_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    category_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    product_tag TEXT[]
);

-- Create index on product_tag for better performance
CREATE INDEX idx_products_product_tag ON products USING GIN (product_tag);

-- Insert demo product with product_tag field
INSERT INTO products (id, name, slug, description, price, sale_price, stock_count, image_url, images, rating, review_count, is_active, category_id, product_tag) VALUES
('f7d5889a-c9f4-4be4-a7c1-8b18f7da8835', 'Wild Stone Code Platinum Perfume', 'wild-stone-code-platinum-perfume', 'Premium long-lasting perfume with masculine woody notes. Sophisticated fragrance for special occasions.', 485.00, 450.00, 85, 'https://codegrooming.com/cdn/shop/files/Platinum_c369f7b9-b1dd-42f0-bcbe-39d347e1ae5d.png?v=1713529441', '{"https://codegrooming.com/cdn/shop/files/Platinum_c369f7b9-b1dd-42f0-bcbe-39d347e1ae5d.png?v=1713529441"}', 4.50, 189, true, '989f2c88-5868-4074-8f7a-ff52f58a320a', '{"perfume", "masculine", "woody", "long-lasting", "premium", "fragrance", "cologne", "scent"}');

-- Add more demo products for better testing
INSERT INTO products (id, name, slug, description, price, sale_price, stock_count, image_url, images, rating, review_count, is_active, category_id, product_tag) VALUES
('12345678-1234-1234-1234-123456789012', 'Premium Leather Wallet', 'premium-leather-wallet', 'Handcrafted genuine leather wallet with multiple card slots and coin pocket. Perfect for daily use.', 299.00, 249.00, 45, 'https://example.com/wallet.jpg', '{"https://example.com/wallet.jpg"}', 4.3, 92, true, '989f2c88-5868-4074-8f7a-ff52f58a321b', '{"wallet", "leather", "premium", "accessories", "men", "fashion", "handcrafted"}');

INSERT INTO products (id, name, slug, description, price, sale_price, stock_count, image_url, images, rating, review_count, is_active, category_id, product_tag) VALUES
('87654321-4321-4321-4321-210987654321', 'Wireless Bluetooth Headphones', 'wireless-bluetooth-headphones', 'High-quality wireless headphones with noise cancellation and 20-hour battery life.', 1299.00, 999.00, 67, 'https://example.com/headphones.jpg', '{"https://example.com/headphones.jpg"}', 4.7, 156, true, '989f2c88-5868-4074-8f7a-ff52f58a321c', '{"headphones", "wireless", "bluetooth", "audio", "music", "noise-cancelling", "electronics"}');

INSERT INTO products (id, name, slug, description, price, sale_price, stock_count, image_url, images, rating, review_count, is_active, category_id, product_tag) VALUES
('11111111-2222-3333-4444-555555555555', 'Organic Green Tea', 'organic-green-tea', 'Premium organic green tea leaves sourced from high-altitude gardens. Rich in antioxidants.', 149.00, NULL, 120, 'https://example.com/tea.jpg', '{"https://example.com/tea.jpg"}', 4.2, 78, true, '989f2c88-5868-4074-8f7a-ff52f58a321d', '{"tea", "green-tea", "organic", "healthy", "antioxidants", "beverages", "natural"}');
