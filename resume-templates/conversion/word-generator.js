/**
 * Word Document Generator for Resume Templates
 * Converts HTML resume templates to Word documents using html-docx-js
 */

const fs = require('fs').promises;
const path = require('path');
const HTMLtoDOCX = require('html-docx-js');

class WordGenerator {
    constructor() {
        this.defaultOptions = {
            table: { row: { cantSplit: true } },
            footer: true,
            pageNumber: true,
            font: 'Calibri'
        };
    }

    /**
     * Generate Word document from HTML content
     * @param {string} htmlContent - Rendered HTML content
     * @param {Object} options - Document generation options
     * @returns {Promise<Buffer>} Word document buffer
     */
    async generateFromHTML(htmlContent, options = {}) {
        try {
            // Clean HTML for better Word compatibility
            const cleanedHTML = this.cleanHTMLForWord(htmlContent);
            
            // Merge options with defaults
            const docxOptions = {
                ...this.defaultOptions,
                ...options
            };

            // Generate Word document
            const docxBuffer = HTMLtoDOCX.asBlob(cleanedHTML, docxOptions);
            
            return Buffer.from(docxBuffer);
        } catch (error) {
            throw new Error(`Failed to generate Word document: ${error.message}`);
        }
    }

    /**
     * Clean HTML content for better Word compatibility
     * @param {string} htmlContent - Original HTML content
     * @returns {string} Cleaned HTML content
     */
    cleanHTMLForWord(htmlContent) {
        let cleaned = htmlContent;

        // Remove script tags
        cleaned = cleaned.replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '');
        
        // Convert CSS classes to inline styles for better compatibility
        cleaned = this.convertCSSToInline(cleaned);
        
        // Replace unsupported CSS properties
        cleaned = cleaned.replace(/display:\s*grid/gi, 'display: block');
        cleaned = cleaned.replace(/display:\s*flex/gi, 'display: block');
        cleaned = cleaned.replace(/grid-template-columns[^;]+;?/gi, '');
        cleaned = cleaned.replace(/flex[^;]+;?/gi, '');
        cleaned = cleaned.replace(/transform[^;]+;?/gi, '');
        
        // Convert border-radius to border for better compatibility
        cleaned = cleaned.replace(/border-radius[^;]+;?/gi, '');
        
        // Ensure proper paragraph structure
        cleaned = cleaned.replace(/<div([^>]*)>/gi, '<p$1>');
        cleaned = cleaned.replace(/<\/div>/gi, '</p>');
        
        // Clean up multiple consecutive spaces and newlines
        cleaned = cleaned.replace(/\s+/g, ' ');
        cleaned = cleaned.replace(/>\s+</g, '><');
        
        return cleaned;
    }

    /**
     * Convert basic CSS classes to inline styles
     * @param {string} htmlContent - HTML with CSS classes
     * @returns {string} HTML with inline styles
     */
    convertCSSToInline(htmlContent) {
        let converted = htmlContent;
        
        // Basic style conversions for common resume elements
        const styleMap = {
            'section-title': 'font-size: 18px; font-weight: bold; color: #2c3e50; margin-bottom: 12px; border-bottom: 2px solid #2c3e50; padding-bottom: 4px;',
            'job-title': 'font-size: 14px; font-weight: bold; color: #2c5aa0; margin-bottom: 4px;',
            'company': 'font-size: 13px; color: #666; font-style: italic; margin-bottom: 4px;',
            'date-location': 'font-size: 12px; color: #888; font-style: italic;',
            'job-description': 'font-size: 12px; color: #555; margin: 8px 0; line-height: 1.4;',
            'achievements': 'margin: 8px 0; padding-left: 20px;',
            'degree': 'font-size: 14px; font-weight: bold; color: #2c5aa0; margin-bottom: 4px;',
            'school': 'font-size: 13px; color: #666; font-style: italic; margin-bottom: 4px;',
            'skill-list': 'font-size: 12px; color: #555; line-height: 1.4;',
            'summary': 'font-size: 12px; line-height: 1.5; color: #444; margin-bottom: 16px;'
        };

        // Apply inline styles
        Object.entries(styleMap).forEach(([className, styles]) => {
            const regex = new RegExp(`class="[^"]*\\b${className}\\b[^"]*"`, 'gi');
            converted = converted.replace(regex, (match) => {
                return match + ` style="${styles}"`;
            });
        });

        return converted;
    }

    /**
     * Save Word document to file
     * @param {Buffer} docxBuffer - Word document buffer
     * @param {string} outputPath - Output file path
     */
    async saveDocument(docxBuffer, outputPath) {
        try {
            // Ensure output directory exists
            const outputDir = path.dirname(outputPath);
            await fs.mkdir(outputDir, { recursive: true });
            
            // Write document to file
            await fs.writeFile(outputPath, docxBuffer);
        } catch (error) {
            throw new Error(`Failed to save Word document: ${error.message}`);
        }
    }

    /**
     * Generate Word document with custom styling
     * @param {string} htmlContent - HTML content
     * @param {Object} customOptions - Custom document options
     * @returns {Promise<Buffer>} Word document buffer
     */
    async generateWithCustomOptions(htmlContent, customOptions = {}) {
        const mergedOptions = {
            ...this.defaultOptions,
            ...customOptions,
            // Custom margins
            margins: {
                top: 720,    // 0.5 inches in twips (1 inch = 1440 twips)
                bottom: 720,
                left: 720,
                right: 720,
                ...customOptions.margins
            },
            // Custom font settings
            font: customOptions.font || 'Calibri',
            fontSize: customOptions.fontSize || 11
        };

        return this.generateFromHTML(htmlContent, mergedOptions);
    }

    /**
     * Add header and footer to Word document
     * @param {string} htmlContent - HTML content
     * @param {Object} headerFooterOptions - Header/footer options
     * @returns {Promise<Buffer>} Word document buffer
     */
    async generateWithHeaderFooter(htmlContent, headerFooterOptions = {}) {
        const { header, footer } = headerFooterOptions;
        
        let modifiedHTML = htmlContent;
        
        // Add header if specified
        if (header) {
            modifiedHTML = `
                <div style="text-align: center; border-bottom: 1px solid #ccc; padding-bottom: 10px; margin-bottom: 20px;">
                    ${header}
                </div>
                ${modifiedHTML}
            `;
        }
        
        // Add footer if specified
        if (footer) {
            modifiedHTML = `
                ${modifiedHTML}
                <div style="text-align: center; border-top: 1px solid #ccc; padding-top: 10px; margin-top: 20px; font-size: 10px; color: #888;">
                    ${footer}
                </div>
            `;
        }
        
        return this.generateFromHTML(modifiedHTML);
    }

    /**
     * Generate Word document optimized for ATS systems
     * @param {string} htmlContent - HTML content
     * @returns {Promise<Buffer>} ATS-optimized Word document buffer
     */
    async generateATSOptimized(htmlContent) {
        // Clean HTML more aggressively for ATS compatibility
        let atsHTML = htmlContent;
        
        // Remove all CSS styling
        atsHTML = atsHTML.replace(/<style[^>]*>[\s\S]*?<\/style>/gi, '');
        atsHTML = atsHTML.replace(/style="[^"]*"/gi, '');
        
        // Remove classes and IDs
        atsHTML = atsHTML.replace(/class="[^"]*"/gi, '');
        atsHTML = atsHTML.replace(/id="[^"]*"/gi, '');
        
        // Convert to simple structure
        atsHTML = atsHTML.replace(/<div[^>]*>/gi, '<p>');
        atsHTML = atsHTML.replace(/<\/div>/gi, '</p>');
        atsHTML = atsHTML.replace(/<span[^>]*>/gi, '');
        atsHTML = atsHTML.replace(/<\/span>/gi, '');
        
        // Ensure proper headings
        atsHTML = atsHTML.replace(/<h[1-6][^>]*>/gi, '<h2>');
        atsHTML = atsHTML.replace(/<\/h[1-6]>/gi, '</h2>');
        
        const atsOptions = {
            font: 'Arial',
            fontSize: 11,
            table: { row: { cantSplit: true } },
            margins: {
                top: 720,
                bottom: 720,
                left: 720,
                right: 720
            }
        };
        
        return this.generateFromHTML(atsHTML, atsOptions);
    }

    /**
     * Get available document options
     * @returns {Object} Available options
     */
    getAvailableOptions() {
        return {
            fonts: ['Calibri', 'Arial', 'Times New Roman', 'Georgia', 'Verdana'],
            fontSizes: [9, 10, 11, 12, 13, 14, 16, 18],
            margins: {
                narrow: { top: 360, bottom: 360, left: 360, right: 360 }, // 0.25 inch
                standard: { top: 720, bottom: 720, left: 720, right: 720 }, // 0.5 inch
                wide: { top: 1440, bottom: 1440, left: 1440, right: 1440 } // 1 inch
            }
        };
    }
}

module.exports = WordGenerator;