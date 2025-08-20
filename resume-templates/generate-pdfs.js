/**
 * Generate PDFs from HTML templates using Puppeteer
 */

const puppeteer = require('puppeteer');
const fs = require('fs').promises;
const path = require('path');

async function generatePDFs() {
    console.log('🚀 Starting PDF generation...\n');
    
    const browser = await puppeteer.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    
    const page = await browser.newPage();
    
    const templates = [
        {
            name: 'classic-one-column',
            displayName: 'Classic One Column',
            path: './outputs/classic-one-column-rendered.html'
        },
        {
            name: 'modern-two-column',
            displayName: 'Modern Two Column',
            path: './outputs/modern-two-column-rendered.html'
        },
        {
            name: 'white-space-emphasis',
            displayName: 'White Space Emphasis',
            path: './outputs/white-space-emphasis-rendered.html'
        }
    ];
    
    for (const template of templates) {
        try {
            console.log(`📄 Generating PDF for ${template.displayName}...`);
            
            // Navigate to the HTML file
            const htmlPath = path.resolve(template.path);
            await page.goto(`file://${htmlPath}`, { waitUntil: 'networkidle0' });
            
            // Generate PDF
            const pdfPath = `./outputs/${template.name}.pdf`;
            await page.pdf({
                path: pdfPath,
                format: 'A4',
                printBackground: true,
                margin: {
                    top: '0.5in',
                    right: '0.5in',
                    bottom: '0.5in',
                    left: '0.5in'
                }
            });
            
            console.log(`✅ PDF saved: ${pdfPath}`);
            
        } catch (error) {
            console.log(`❌ Error generating PDF for ${template.displayName}:`, error.message);
        }
    }
    
    await browser.close();
    console.log('\n🎉 PDF generation completed!');
}

// Run if called directly
if (require.main === module) {
    generatePDFs().catch(error => {
        console.error('PDF generation failed:', error);
        process.exit(1);
    });
}

module.exports = { generatePDFs };