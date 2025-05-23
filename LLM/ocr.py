#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import requests
import tempfile
from pathlib import Path
from urllib.parse import urlparse
import logging
from pdf2image import convert_from_path, convert_from_bytes
import pytesseract
import cv2
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set Tesseract executable path explicitly
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class PdfOcrConverter:
    def __init__(self, output_dir="markdown_pages/pdf"):
        """Initialize the PDF OCR converter with the output directory."""
        self.output_dir = output_dir
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)

    def download_pdf(self, url):
        """Download PDF from URL and return the content."""
        logger.info(f"Downloading PDF from {url}")
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException as e:
            logger.error(f"Error downloading PDF: {e}")
            raise

    def get_pdf_content(self, pdf_source):
        """Get PDF content from URL or local file."""
        if pdf_source.startswith(('http://', 'https://')):
            return self.download_pdf(pdf_source), os.path.basename(urlparse(pdf_source).path)
        else:
            # Local file
            with open(pdf_source, 'rb') as f:
                return f.read(), os.path.basename(pdf_source)

    def convert_pdf_to_images(self, pdf_content):
        """Convert PDF content to images."""
        logger.info("Converting PDF to images")
        try:
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_file.write(pdf_content)
                temp_file_path = temp_file.name

            poppler_path = r"C:\Program Files\poppler-24.08.0\Library\bin"
            logger.info(f"Using Poppler path: {poppler_path}")
            
            images = convert_from_path(temp_file_path, dpi=300, poppler_path=poppler_path)
            os.unlink(temp_file_path)
            
            logger.info(f"Converted PDF to {len(images)} images")
            return images
        except Exception as e:
            logger.error(f"Error converting PDF to images: {e}")
            raise

    def detect_and_extract_tables(self, image):
        """Detect tables in an image and extract their content."""
        image_np = np.array(image)
        image_cv = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
        
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 25))
        
        horizontal_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
        vertical_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, vertical_kernel, iterations=2)
        
        table_mask = cv2.add(horizontal_lines, vertical_lines)
        contours, _ = cv2.findContours(table_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        extracted_tables = []
        for i, contour in enumerate(contours):
            x, y, w, h = cv2.boundingRect(contour)
            if w > 100 and h > 100:
                table_region = image.crop((x, y, x+w, y+h))
                table_data = self.extract_table_content(table_region)
                extracted_tables.append({
                    'id': i+1,
                    'region': (x, y, x+w, y+h),
                    'data': table_data
                })
        return extracted_tables
    
    def extract_table_content(self, table_image):
        """Extract the content of a table from its image."""
        table_np = np.array(table_image)
        table_cv = cv2.cvtColor(table_np, cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(table_cv, cv2.COLOR_BGR2GRAY)
        binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
        
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        dilated = cv2.dilate(binary, kernel, iterations=1)
        
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 1))
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 20))
        
        horizontal_lines = cv2.morphologyEx(dilated, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
        vertical_lines = cv2.morphologyEx(dilated, cv2.MORPH_OPEN, vertical_kernel, iterations=2)
        
        table_structure = cv2.add(horizontal_lines, vertical_lines)
        contours, _ = cv2.findContours(table_structure, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        def sort_contours(cnts):
            sorted_by_y = sorted(cnts, key=lambda c: cv2.boundingRect(c)[1])
            rows = []
            current_row = [sorted_by_y[0]]
            y_thresh = 10
            
            for cnt in sorted_by_y[1:]:
                _, y, _, _ = cv2.boundingRect(cnt)
                _, prev_y, _, _ = cv2.boundingRect(current_row[0])
                if abs(y - prev_y) <= y_thresh:
                    current_row.append(cnt)
                else:
                    rows.append(sorted(current_row, key=lambda c: cv2.boundingRect(c)[0]))
                    current_row = [cnt]
            if current_row:
                rows.append(sorted(current_row, key=lambda c: cv2.boundingRect(c)[0]))
            return rows
        
        try:
            sorted_cells = sort_contours(contours)
        except Exception as e:
            logger.warning(f"Failed to sort table cells: {e}")
            return [["[Table content could not be extracted properly]"]]
        
        table_data = []
        for row in sorted_cells:
            row_data = []
            for cell in row:
                x, y, w, h = cv2.boundingRect(cell)
                cell_image = table_image.crop((x, y, x+w, y+h))
                cell_text = pytesseract.image_to_string(cell_image, lang='cat+spa+eng').strip()
                row_data.append(cell_text if cell_text else " ")
            if row_data:
                table_data.append(row_data)
        
        if not table_data:
            return [["[Table detected but content extraction failed]"]]
        return table_data

    def extract_text_from_image(self, image):
        """Extract text from a single image using pytesseract."""
        image_np = np.array(image)
        text = pytesseract.image_to_string(image_np, lang='cat+spa+eng')
        return text

    def extract_content_from_pdf(self, pdf_content):
        """Extract content (text, tables, etc.) from PDF."""
        images = self.convert_pdf_to_images(pdf_content)
        all_page_content = []
        
        for i, image in enumerate(images):
            logger.info(f"Processing page {i+1}/{len(images)}")
            text = self.extract_text_from_image(image)
            tables = self.detect_and_extract_tables(image)
            page_content = {
                'page_num': i+1,
                'text': text,
                'tables': tables
            }
            all_page_content.append(page_content)
        return all_page_content

    def content_to_markdown(self, all_page_content):
        """Convert extracted content to Markdown format."""
        md_content = []
        for page in all_page_content:
            md_content.append(f"## Página {page['page_num']}\n")
            text_lines = page['text'].split('\n')
            current_paragraph = []
            
            for line in text_lines:
                line = line.strip()
                if not line:
                    if current_paragraph:
                        md_content.append(' '.join(current_paragraph))
                        md_content.append('\n')
                        current_paragraph = []
                else:
                    current_paragraph.append(line)
            if current_paragraph:
                md_content.append(' '.join(current_paragraph))
                md_content.append('\n')
            
            if page['tables']:
                md_content.append("\n### Tablas detectadas en esta página:\n")
                for table in page['tables']:
                    md_content.append(f"\n**Tabla {table['id']}:**\n\n")
                    if table['data'] and len(table['data']) > 0:
                        max_cols = max(len(row) for row in table['data'])
                        md_content.append("| " + " | ".join(["Columna " + str(i+1) for i in range(max_cols)]) + " |\n")
                        md_content.append("| " + " | ".join(["---" for _ in range(max_cols)]) + " |\n")
                        for row in table['data']:
                            padded_row = row + ["" for _ in range(max_cols - len(row))]
                            md_content.append("| " + " | ".join(padded_row) + " |\n")
                    else:
                        md_content.append("*No se pudo extraer el contenido de la tabla*\n")
            md_content.append("\n---\n")
        return "\n".join(md_content)

    def process_pdf(self, pdf_source):
        """Process a single PDF file and convert it to Markdown."""
        try:
            pdf_content, pdf_filename = self.get_pdf_content(pdf_source)
            base_filename = os.path.splitext(pdf_filename)[0]
            logger.info(f"Extracting content from {pdf_filename}...")
            all_content = self.extract_content_from_pdf(pdf_content)
            logger.info("Converting content to Markdown...")
            md_content = self.content_to_markdown(all_content)
            output_path = os.path.join(self.output_dir, f"{base_filename}.md")
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            logger.info(f"Successfully converted PDF to Markdown: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_source}: {e}")
            raise

def process_pdf_folder(input_folder, output_dir='markdown_pages/pdf'):
    """Process all PDF files in a folder and convert them to Markdown."""
    converter = PdfOcrConverter(output_dir=output_dir)
    
    # Ensure input folder exists
    if not os.path.exists(input_folder):
        return f"Error: Input folder '{input_folder}' does not exist"
    
    # Get all PDF files in the folder
    pdf_files = [f for f in os.listdir(input_folder) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        return f"No PDF files found in '{input_folder}'"
    
    results = []
    for pdf_file in pdf_files:
        pdf_path = os.path.join(input_folder, pdf_file)
        try:
            output_path = converter.process_pdf(pdf_path)
            results.append(f"Successfully converted '{pdf_file}' to: {output_path}")
        except Exception as e:
            results.append(f"Error converting '{pdf_file}': {e}")
    
    return "\n".join(results)

# Example usage
if __name__ == "__main__":
    input_folder = "./pdf_pages"  # Change this to your input folder path
    output_folder = "./pdfoutput"  # Change this to your output folder path
    result = process_pdf_folder(input_folder, output_folder)
    print(result)