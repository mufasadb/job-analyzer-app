/**
 * PDF Generator for Resume Templates
 * Converts HTML resume templates to PDF using Puppeteer
 */

const puppeteer = require('puppeteer');
const fs = require('fs').promises;
const path = require('path');

class PDFGenerator {
    constructor() {
        this.browserInstance = null;
    }

    /**
     * Initialize browser instance
     * @returns {Promise<Browser>} Puppeteer browser instance
     */
    async getBrowser() {
        if (!this.browserInstance) {
            this.browserInstance = await puppeteer.launch({
                headless: 'new',
                args: [
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu'
                ]
            });
        }
        return this.browserInstance;
    }

    /**
     * Generate PDF from HTML content
     * @param {string} htmlContent - Rendered HTML content
     * @param {Object} options - PDF generation options
     * @returns {Promise<Buffer>} PDF buffer
     */
    async generateFromHTML(htmlContent, options = {}) {
        const browser = await this.getBrowser();
        const page = await browser.newPage();

        try {
            // Set content and wait for any external resources
            await page.setContent(htmlContent, { 
                waitUntil: 'networkidle0',
                timeout: 30000 
            });

            // Configure PDF options
            const pdfOptions = {
                format: 'A4',
                printBackground: true,
                margin: {
                    top: '0.5in',
                    right: '0.5in',
                    bottom: '0.5in',
                    left: '0.5in'
                },
                ...options
            };

            // Generate PDF
            const pdfBuffer = await page.pdf(pdfOptions);
            
            return pdfBuffer;
        } catch (error) {
            throw new Error(`Failed to generate PDF: ${error.message}`);
        } finally {
            await page.close();
        }
    }

    /**
     * Generate PDF from HTML file
     * @param {string} htmlFilePath - Path to HTML file
     * @param {Object} options - PDF generation options
     * @returns {Promise<Buffer>} PDF buffer
     */
    async generateFromFile(htmlFilePath, options = {}) {
        const browser = await this.getBrowser();
        const page = await browser.newPage();

        try {
            // Convert to file URL for local files
            const fileUrl = `file://${path.resolve(htmlFilePath)}`;
            
            await page.goto(fileUrl, { 
                waitUntil: 'networkidle0',
                timeout: 30000 
            });

            // Configure PDF options
            const pdfOptions = {
                format: 'A4',
                printBackground: true,
                margin: {
                    top: '0.5in',
                    right: '0.5in',
                    bottom: '0.5in',
                    left: '0.5in'
                },
                ...options
            };

            // Generate PDF
            const pdfBuffer = await page.pdf(pdfOptions);
            
            return pdfBuffer;
        } catch (error) {
            throw new Error(`Failed to generate PDF from file: ${error.message}`);
        } finally {
            await page.close();
        }
    }

    /**
     * Save PDF to file
     * @param {Buffer} pdfBuffer - PDF buffer
     * @param {string} outputPath - Output file path
     */
    async savePDF(pdfBuffer, outputPath) {
        try {
            // Ensure output directory exists
            const outputDir = path.dirname(outputPath);
            await fs.mkdir(outputDir, { recursive: true });
            
            // Write PDF to file
            await fs.writeFile(outputPath, pdfBuffer);
        } catch (error) {
            throw new Error(`Failed to save PDF: ${error.message}`);
        }
    }

    /**
     * Take screenshot of HTML content for preview
     * @param {string} htmlContent - Rendered HTML content
     * @param {Object} options - Screenshot options
     * @returns {Promise<Buffer>} Screenshot buffer
     */
    async takeScreenshot(htmlContent, options = {}) {
        const browser = await this.getBrowser();
        const page = await browser.newPage();

        try {
            // Set viewport for consistent screenshots
            await page.setViewport({
                width: 1200,
                height: 1600,
                deviceScaleFactor: 2
            });

            // Set content and wait for resources
            await page.setContent(htmlContent, { 
                waitUntil: 'networkidle0',
                timeout: 30000 
            });

            // Configure screenshot options
            const screenshotOptions = {
                type: 'png',
                fullPage: true,
                ...options
            };

            // Take screenshot
            const screenshotBuffer = await page.screenshot(screenshotOptions);
            
            return screenshotBuffer;
        } catch (error) {
            throw new Error(`Failed to take screenshot: ${error.message}`);
        } finally {
            await page.close();
        }
    }

    /**
     * Generate PDF with custom CSS for print optimization
     * @param {string} htmlContent - HTML content
     * @param {string} customCSS - Additional CSS for print
     * @param {Object} options - PDF options
     * @returns {Promise<Buffer>} PDF buffer
     */
    async generateWithCustomCSS(htmlContent, customCSS = '', options = {}) {
        const browser = await this.getBrowser();
        const page = await browser.newPage();

        try {
            // Add print-specific CSS
            const printCSS = `
                @media print {
                    * {
                        -webkit-print-color-adjust: exact !important;
                        color-adjust: exact !important;
                        print-color-adjust: exact !important;
                    }
                    
                    body {
                        margin: 0;
                        padding: 0;
                    }
                    
                    .page-break {
                        page-break-before: always;
                    }
                    
                    .no-page-break {
                        page-break-inside: avoid;
                    }
                }
                ${customCSS}
            `;

            // Inject custom CSS
            const htmlWithCSS = htmlContent.replace(
                '</head>',
                `<style>${printCSS}</style></head>`
            );

            await page.setContent(htmlWithCSS, { 
                waitUntil: 'networkidle0',
                timeout: 30000 
            });

            // Configure PDF options
            const pdfOptions = {
                format: 'A4',
                printBackground: true,
                margin: {
                    top: '0.5in',
                    right: '0.5in',
                    bottom: '0.5in',
                    left: '0.5in'
                },
                ...options
            };

            const pdfBuffer = await page.pdf(pdfOptions);
            return pdfBuffer;
        } catch (error) {
            throw new Error(`Failed to generate PDF with custom CSS: ${error.message}`);
        } finally {
            await page.close();
        }
    }

    /**
     * Close browser instance
     */
    async closeBrowser() {
        if (this.browserInstance) {
            await this.browserInstance.close();
            this.browserInstance = null;
        }
    }

    /**
     * Get available PDF formats and options
     * @returns {Object} Available options
     */
    getAvailableOptions() {
        return {
            formats: ['A4', 'A3', 'A5', 'Legal', 'Letter', 'Tabloid'],
            margins: {
                none: { top: 0, right: 0, bottom: 0, left: 0 },
                minimal: { top: '0.25in', right: '0.25in', bottom: '0.25in', left: '0.25in' },
                standard: { top: '0.5in', right: '0.5in', bottom: '0.5in', left: '0.5in' },
                generous: { top: '1in', right: '1in', bottom: '1in', left: '1in' }
            },
            orientations: ['portrait', 'landscape']
        };
    }
}

module.exports = PDFGenerator;