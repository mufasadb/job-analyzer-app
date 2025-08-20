/**
 * Generate DOCX files from HTML templates using html-docx-js
 */

const fs = require('fs').promises;
const path = require('path');
const { asBlob } = require('html-docx-js');

async function generateDOCX() {
    console.log('🚀 Starting DOCX generation...\n');
    
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
            console.log(`📄 Generating DOCX for ${template.displayName}...`);
            
            // Read HTML file
            const htmlContent = await fs.readFile(template.path, 'utf-8');
            
            // Convert to DOCX using asBlob
            const docxBlob = asBlob(htmlContent);
            
            // Convert blob to buffer
            const arrayBuffer = await docxBlob.arrayBuffer();
            const docxBuffer = Buffer.from(arrayBuffer);
            
            // Save DOCX file
            const docxPath = `./outputs/${template.name}.docx`;
            await fs.writeFile(docxPath, docxBuffer);
            
            console.log(`✅ DOCX saved: ${docxPath} (${docxBuffer.length} bytes)`);
            
        } catch (error) {
            console.log(`❌ Error generating DOCX for ${template.displayName}:`, error.message);
        }
    }
    
    console.log('\n🎉 DOCX generation completed!');
}

// Run if called directly
if (require.main === module) {
    generateDOCX().catch(error => {
        console.error('DOCX generation failed:', error);
        process.exit(1);
    });
}

module.exports = { generateDOCX };