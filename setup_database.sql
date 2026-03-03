-- Run this SQL against your Azure Database for MySQL Flexible Server
-- to create the sample database used by the AI agent.

CREATE DATABASE IF NOT EXISTS demo_sales;
USE demo_sales;

CREATE TABLE IF NOT EXISTS customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),
    city VARCHAR(50),
    signup_date DATE
);

CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT,
    product VARCHAR(100),
    amount DECIMAL(10,2),
    order_date DATE,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

INSERT INTO customers (name, email, city, signup_date) VALUES
('Sara Ahmed', 'sara@example.com', 'Cairo', '2024-06-15'),
('John Smith', 'john@example.com', 'London', '2024-08-22'),
('Priya Patel', 'priya@example.com', 'Mumbai', '2025-01-10');

INSERT INTO orders (customer_id, product, amount, order_date) VALUES
(1, 'Azure Certification Voucher', 150.00, '2025-03-01'),
(2, 'MySQL Workbench Pro License', 99.00, '2025-03-10'),
(1, 'Power BI Dashboard Template', 45.00, '2025-04-05'),
(3, 'Data Analysis Course', 200.00, '2025-05-20');
