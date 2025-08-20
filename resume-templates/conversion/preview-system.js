/**
 * Preview System for Resume Templates
 * Handles template preview, screenshot generation, and user confirmation
 */

const fs = require('fs').promises;
const path = require('path');
const TemplateRenderer = require('./template-renderer');
const PDFGenerator = require('./pdf-generator');

class PreviewSystem {
    constructor() {
        this.renderer = new TemplateRenderer();
        this.pdfGenerator = new PDFGenerator();
        this.previewsDir = path.join(__dirname, '../screenshots');
    }

    /**
     * Initialize preview system
     */
    async init() {
        // Ensure screenshots directory exists
        await fs.mkdir(this.previewsDir, { recursive: true });
    }

    /**
     * Generate preview of a template with data
     * @param {string} templatePath - Path to template file
     * @param {Object} resumeData - Resume data
     * @param {Object} options - Preview options
     * @returns {Object} Preview result with HTML and screenshot path
     */
    async generatePreview(templatePath, resumeData, options = {}) {
        try {
            // Render template with data
            const html = await this.renderer.render(templatePath, resumeData);
            
            // Generate timestamp for unique filenames
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            const templateName = path.basename(templatePath, '.html');
            
            // Take screenshot
            const screenshotBuffer = await this.pdfGenerator.takeScreenshot(html, {
                type: 'png',
                fullPage: true,
                ...options.screenshot
            });
            
            // Save screenshot
            const screenshotPath = path.join(
                this.previewsDir, 
                `${templateName}-preview-${timestamp}.png`
            );
            await fs.writeFile(screenshotPath, screenshotBuffer);
            
            // Save rendered HTML for reference
            const htmlPath = path.join(
                this.previewsDir,
                `${templateName}-preview-${timestamp}.html`
            );
            await fs.writeFile(htmlPath, html);
            
            return {
                success: true,
                templateName: templateName,
                html: html,
                htmlPath: htmlPath,
                screenshotPath: screenshotPath,
                timestamp: timestamp,
                previewUrl: `file://${screenshotPath}`
            };
        } catch (error) {
            return {
                success: false,
                error: error.message,
                templatePath: templatePath
            };
        }
    }

    /**
     * Generate previews for multiple templates
     * @param {Array} templatePaths - Array of template paths
     * @param {Object} resumeData - Resume data
     * @param {Object} options - Preview options
     * @returns {Array} Array of preview results
     */
    async generateMultiplePreviews(templatePaths, resumeData, options = {}) {
        const previews = [];
        
        for (const templatePath of templatePaths) {
            const preview = await this.generatePreview(templatePath, resumeData, options);
            previews.push(preview);
        }
        
        return previews;
    }

    /**
     * Generate preview for all templates in a category
     * @param {string} category - Template category (simple, complex, photo)
     * @param {Object} resumeData - Resume data
     * @param {Object} options - Preview options
     * @returns {Array} Array of preview results
     */
    async generateCategoryPreviews(category, resumeData, options = {}) {
        const templatesDir = path.join(__dirname, '../templates', category);
        
        try {
            const files = await fs.readdir(templatesDir);
            const htmlFiles = files.filter(file => file.endsWith('.html'));
            const templatePaths = htmlFiles.map(file => path.join(templatesDir, file));
            
            return await this.generateMultiplePreviews(templatePaths, resumeData, options);
        } catch (error) {
            throw new Error(`Failed to generate category previews: ${error.message}`);
        }
    }

    /**
     * Create comparison view of multiple templates
     * @param {Array} templatePaths - Array of template paths
     * @param {Object} resumeData - Resume data
     * @returns {string} HTML comparison view
     */
    async createComparisonView(templatePaths, resumeData) {
        const previews = await this.generateMultiplePreviews(templatePaths, resumeData);
        const successfulPreviews = previews.filter(p => p.success);
        
        const comparisonHTML = `
            <!DOCTYPE html>
            <html>
            <head>
                <title>Resume Template Comparison</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        margin: 20px;
                        background: #f5f5f5;
                    }
                    .comparison-container {
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
                        gap: 20px;
                        max-width: 1400px;
                        margin: 0 auto;
                    }
                    .template-preview {
                        background: white;
                        border-radius: 8px;
                        padding: 20px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    }
                    .template-title {
                        font-size: 18px;
                        font-weight: bold;
                        margin-bottom: 15px;
                        color: #333;
                        text-align: center;
                    }
                    .template-screenshot {
                        width: 100%;
                        height: auto;
                        border: 1px solid #ddd;
                        border-radius: 4px;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    }
                    .template-actions {
                        margin-top: 15px;
                        text-align: center;
                    }
                    .btn {
                        display: inline-block;
                        padding: 8px 16px;
                        margin: 0 5px;
                        background: #007bff;
                        color: white;
                        text-decoration: none;
                        border-radius: 4px;
                        font-size: 14px;
                    }
                    .btn:hover {
                        background: #0056b3;
                    }
                    .btn-secondary {
                        background: #6c757d;
                    }
                    .btn-secondary:hover {
                        background: #545b62;
                    }
                    h1 {
                        text-align: center;
                        color: #333;
                        margin-bottom: 30px;
                    }
                </style>
            </head>
            <body>
                <h1>Resume Template Comparison</h1>
                <div class="comparison-container">
                    ${successfulPreviews.map(preview => `
                        <div class="template-preview">
                            <div class="template-title">${this.renderer.formatDisplayName(preview.templateName)}</div>
                            <img src="file://${preview.screenshotPath}" alt="${preview.templateName} preview" class="template-screenshot">
                            <div class="template-actions">
                                <a href="file://${preview.htmlPath}" class="btn" target="_blank">View HTML</a>
                                <a href="file://${preview.screenshotPath}" class="btn btn-secondary" target="_blank">Full Size</a>
                            </div>
                        </div>
                    `).join('')}
                </div>
                
                <script>
                    // Add click handlers for template selection
                    document.querySelectorAll('.template-preview').forEach((preview, index) => {
                        preview.addEventListener('click', function() {
                            // Remove previous selections
                            document.querySelectorAll('.template-preview').forEach(p => {
                                p.style.border = 'none';
                                p.style.boxShadow = '0 2px 10px rgba(0,0,0,0.1)';
                            });
                            
                            // Highlight selected
                            this.style.border = '3px solid #007bff';
                            this.style.boxShadow = '0 4px 15px rgba(0,123,255,0.3)';
                            
                            // Store selection
                            localStorage.setItem('selectedTemplate', '${successfulPreviews[index]?.templateName}');
                            
                            console.log('Selected template:', '${successfulPreviews[index]?.templateName}');
                        });
                    });
                    
                    // Restore previous selection if any
                    const selectedTemplate = localStorage.getItem('selectedTemplate');
                    if (selectedTemplate) {
                        const templateElements = document.querySelectorAll('.template-preview');
                        templateElements.forEach(element => {
                            const title = element.querySelector('.template-title').textContent;
                            if (title.toLowerCase().includes(selectedTemplate.toLowerCase())) {
                                element.click();
                            }
                        });
                    }
                </script>
            </body>
            </html>
        `;
        
        // Save comparison view
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const comparisonPath = path.join(this.previewsDir, `comparison-${timestamp}.html`);
        await fs.writeFile(comparisonPath, comparisonHTML);
        
        return comparisonPath;
    }

    /**
     * Generate mobile preview of a template
     * @param {string} templatePath - Path to template file
     * @param {Object} resumeData - Resume data
     * @returns {Object} Mobile preview result
     */
    async generateMobilePreview(templatePath, resumeData) {
        const mobileOptions = {
            screenshot: {
                type: 'png',
                fullPage: true,
                // Mobile viewport simulation
                clip: {
                    x: 0,
                    y: 0,
                    width: 375,  // iPhone viewport width
                    height: 2000 // Enough height to capture content
                }
            }
        };
        
        const preview = await this.generatePreview(templatePath, resumeData, mobileOptions);
        
        // Update paths to indicate mobile version
        if (preview.success) {
            const mobileScreenshotPath = preview.screenshotPath.replace('.png', '-mobile.png');
            await fs.rename(preview.screenshotPath, mobileScreenshotPath);
            preview.screenshotPath = mobileScreenshotPath;
            preview.previewUrl = `file://${mobileScreenshotPath}`;
        }
        
        return preview;
    }

    /**
     * Clean up old preview files
     * @param {number} maxAge - Maximum age in hours (default: 24)
     */
    async cleanupOldPreviews(maxAge = 24) {
        try {
            const files = await fs.readdir(this.previewsDir);
            const now = Date.now();
            const maxAgeMs = maxAge * 60 * 60 * 1000;
            
            for (const file of files) {
                const filePath = path.join(this.previewsDir, file);
                const stats = await fs.stat(filePath);
                
                if (now - stats.mtime.getTime() > maxAgeMs) {
                    await fs.unlink(filePath);
                    console.log(`Cleaned up old preview file: ${file}`);
                }
            }
        } catch (error) {
            console.error('Failed to cleanup old previews:', error.message);
        }
    }

    /**
     * Get list of all generated previews
     * @returns {Array} List of preview files with metadata
     */
    async getGeneratedPreviews() {
        try {
            const files = await fs.readdir(this.previewsDir);
            const previews = [];
            
            for (const file of files) {
                if (file.endsWith('.png') || file.endsWith('.html')) {
                    const filePath = path.join(this.previewsDir, file);
                    const stats = await fs.stat(filePath);
                    
                    previews.push({
                        filename: file,
                        path: filePath,
                        size: stats.size,
                        created: stats.birthtime,
                        modified: stats.mtime,
                        type: path.extname(file)
                    });
                }
            }
            
            return previews.sort((a, b) => b.created - a.created);
        } catch (error) {
            throw new Error(`Failed to get preview list: ${error.message}`);
        }
    }

    /**
     * Close resources
     */
    async close() {
        await this.pdfGenerator.closeBrowser();
    }
}

module.exports = PreviewSystem;