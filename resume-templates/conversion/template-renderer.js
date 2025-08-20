/**
 * Template Renderer for Resume Templates
 * Handles rendering HTML templates with JSON data
 */

const fs = require('fs').promises;
const path = require('path');
const Handlebars = require('handlebars');

class TemplateRenderer {
    constructor() {
        this.templates = new Map();
        this.registerHelpers();
    }

    /**
     * Register Handlebars helpers
     */
    registerHelpers() {
        // Helper to join arrays
        Handlebars.registerHelper('join', function(array, separator) {
            if (Array.isArray(array)) {
                return array.join(separator || ', ');
            }
            return '';
        });

        // Helper for conditional logic
        Handlebars.registerHelper('ifEquals', function(arg1, arg2, options) {
            return (arg1 == arg2) ? options.fn(this) : options.inverse(this);
        });

        // Helper for date formatting
        Handlebars.registerHelper('formatDate', function(dateString) {
            if (!dateString) return '';
            const date = new Date(dateString);
            return date.toLocaleDateString('en-US', { 
                year: 'numeric', 
                month: 'short' 
            });
        });

        // Helper to check if array has items
        Handlebars.registerHelper('hasItems', function(array, options) {
            if (array && array.length > 0) {
                return options.fn(this);
            }
            return options.inverse(this);
        });

        // Helper to get first N items from array
        Handlebars.registerHelper('limit', function(array, limit) {
            if (!Array.isArray(array)) return [];
            return array.slice(0, limit);
        });
    }

    /**
     * Load and cache a template
     * @param {string} templatePath - Path to the HTML template file
     * @returns {Function} Compiled Handlebars template
     */
    async loadTemplate(templatePath) {
        const fullPath = path.resolve(templatePath);
        
        if (this.templates.has(fullPath)) {
            return this.templates.get(fullPath);
        }

        try {
            const templateContent = await fs.readFile(fullPath, 'utf8');
            const compiledTemplate = Handlebars.compile(templateContent);
            this.templates.set(fullPath, compiledTemplate);
            return compiledTemplate;
        } catch (error) {
            throw new Error(`Failed to load template from ${fullPath}: ${error.message}`);
        }
    }

    /**
     * Render a template with data
     * @param {string} templatePath - Path to the HTML template file
     * @param {Object} data - Resume data object
     * @returns {string} Rendered HTML
     */
    async render(templatePath, data) {
        try {
            const template = await this.loadTemplate(templatePath);
            const html = template(data);
            return html;
        } catch (error) {
            throw new Error(`Failed to render template: ${error.message}`);
        }
    }

    /**
     * Load sample data
     * @param {string} dataPath - Path to JSON data file
     * @returns {Object} Resume data object
     */
    async loadData(dataPath) {
        try {
            const dataContent = await fs.readFile(path.resolve(dataPath), 'utf8');
            return JSON.parse(dataContent);
        } catch (error) {
            throw new Error(`Failed to load data from ${dataPath}: ${error.message}`);
        }
    }

    /**
     * Get all available templates
     * @param {string} templatesDir - Path to templates directory
     * @returns {Array} List of available templates
     */
    async getAvailableTemplates(templatesDir = './templates') {
        const templates = [];
        const baseDir = path.resolve(templatesDir);

        try {
            const categories = await fs.readdir(baseDir);
            
            for (const category of categories) {
                const categoryPath = path.join(baseDir, category);
                const stat = await fs.stat(categoryPath);
                
                if (stat.isDirectory()) {
                    const files = await fs.readdir(categoryPath);
                    const htmlFiles = files.filter(file => file.endsWith('.html'));
                    
                    for (const file of htmlFiles) {
                        templates.push({
                            name: path.basename(file, '.html'),
                            category: category,
                            path: path.join(categoryPath, file),
                            displayName: this.formatDisplayName(path.basename(file, '.html'))
                        });
                    }
                }
            }
            
            return templates;
        } catch (error) {
            throw new Error(`Failed to get available templates: ${error.message}`);
        }
    }

    /**
     * Format template name for display
     * @param {string} fileName - Template file name
     * @returns {string} Formatted display name
     */
    formatDisplayName(fileName) {
        return fileName
            .replace(/-/g, ' ')
            .replace(/\b\w/g, l => l.toUpperCase());
    }

    /**
     * Validate resume data against schema
     * @param {Object} data - Resume data
     * @returns {Object} Validation result
     */
    validateData(data) {
        const required = ['personal', 'summary', 'experience', 'education', 'skills'];
        const missing = [];
        const warnings = [];

        // Check required fields
        required.forEach(field => {
            if (!data[field]) {
                missing.push(field);
            }
        });

        // Check personal info
        if (data.personal) {
            const personalRequired = ['name', 'title', 'email', 'phone', 'location'];
            personalRequired.forEach(field => {
                if (!data.personal[field]) {
                    warnings.push(`Missing personal.${field}`);
                }
            });
        }

        // Check experience array
        if (data.experience && Array.isArray(data.experience)) {
            data.experience.forEach((exp, index) => {
                if (!exp.title || !exp.company || !exp.startDate) {
                    warnings.push(`Incomplete experience item at index ${index}`);
                }
            });
        }

        return {
            valid: missing.length === 0,
            missing: missing,
            warnings: warnings
        };
    }

    /**
     * Clear template cache
     */
    clearCache() {
        this.templates.clear();
    }
}

module.exports = TemplateRenderer;