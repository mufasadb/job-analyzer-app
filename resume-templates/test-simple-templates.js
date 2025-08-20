/**
 * Test Script for Simple Resume Templates
 * Tests all three simple templates with sample data
 */

const path = require('path');
const TemplateRenderer = require('./conversion/template-renderer');
const PDFGenerator = require('./conversion/pdf-generator');
const WordGenerator = require('./conversion/word-generator');
const PreviewSystem = require('./conversion/preview-system');

async function testSimpleTemplates() {
    console.log('🧪 Testing Simple Resume Templates...\n');

    const renderer = new TemplateRenderer();
    const pdfGenerator = new PDFGenerator();
    const wordGenerator = new WordGenerator();
    const previewSystem = new PreviewSystem();

    try {
        await previewSystem.init();

        // Load sample data
        console.log('📄 Loading sample data...');
        const sampleData = await renderer.loadData('./data/sample-data.json');
        console.log('✅ Sample data loaded successfully');

        // Validate data
        const validation = renderer.validateData(sampleData);
        if (!validation.valid) {
            console.log('❌ Data validation failed:', validation.missing);
            return;
        }
        if (validation.warnings.length > 0) {
            console.log('⚠️  Data warnings:', validation.warnings);
        }
        console.log('✅ Data validation passed\n');

        // Test templates
        const templates = [
            {
                name: 'Classic One Column',
                path: './templates/simple/classic-one-column.html'
            },
            {
                name: 'Modern Two Column',
                path: './templates/simple/modern-two-column.html'
            },
            {
                name: 'White Space Emphasis',
                path: './templates/simple/white-space-emphasis.html'
            }
        ];

        const results = [];

        for (const template of templates) {
            console.log(`🎨 Testing ${template.name}...`);
            
            try {
                // Render HTML
                const html = await renderer.render(template.path, sampleData);
                console.log(`  ✅ HTML rendered (${html.length} characters)`);

                // Generate preview
                const preview = await previewSystem.generatePreview(template.path, sampleData);
                if (preview.success) {
                    console.log(`  ✅ Screenshot saved: ${path.basename(preview.screenshotPath)}`);
                } else {
                    console.log(`  ❌ Screenshot failed: ${preview.error}`);
                }

                // Generate PDF
                const pdfBuffer = await pdfGenerator.generateFromHTML(html);
                const pdfPath = `./outputs/${template.name.replace(/\s+/g, '-').toLowerCase()}.pdf`;
                await pdfGenerator.savePDF(pdfBuffer, pdfPath);
                console.log(`  ✅ PDF saved: ${path.basename(pdfPath)} (${pdfBuffer.length} bytes)`);

                // Generate Word document
                const docxBuffer = await wordGenerator.generateFromHTML(html);
                const docxPath = `./outputs/${template.name.replace(/\s+/g, '-').toLowerCase()}.docx`;
                await wordGenerator.saveDocument(docxBuffer, docxPath);
                console.log(`  ✅ Word document saved: ${path.basename(docxPath)} (${docxBuffer.length} bytes)`);

                results.push({
                    template: template.name,
                    success: true,
                    html: html.length,
                    pdf: pdfBuffer.length,
                    docx: docxBuffer.length,
                    screenshot: preview.success ? preview.screenshotPath : null
                });

            } catch (error) {
                console.log(`  ❌ Error: ${error.message}`);
                results.push({
                    template: template.name,
                    success: false,
                    error: error.message
                });
            }
            
            console.log(''); // Empty line for readability
        }

        // Generate comparison view
        console.log('🖼️  Generating comparison view...');
        const templatePaths = templates.map(t => t.path);
        const comparisonPath = await previewSystem.createComparisonView(templatePaths, sampleData);
        console.log(`✅ Comparison view saved: ${path.basename(comparisonPath)}`);
        
        // Print summary
        console.log('\n📊 Test Results Summary:');
        console.log('=' .repeat(50));
        
        const successful = results.filter(r => r.success);
        const failed = results.filter(r => !r.success);
        
        console.log(`✅ Successful: ${successful.length}/${results.length}`);
        console.log(`❌ Failed: ${failed.length}/${results.length}`);
        
        if (successful.length > 0) {
            console.log('\nSuccessful Templates:');
            successful.forEach(result => {
                console.log(`  • ${result.template}`);
                console.log(`    HTML: ${result.html} chars | PDF: ${result.pdf} bytes | DOCX: ${result.docx} bytes`);
            });
        }
        
        if (failed.length > 0) {
            console.log('\nFailed Templates:');
            failed.forEach(result => {
                console.log(`  • ${result.template}: ${result.error}`);
            });
        }

        console.log(`\n🎉 Template testing completed!`);
        console.log(`📁 Check outputs in: ./outputs/`);
        console.log(`📸 Check screenshots in: ./screenshots/`);
        console.log(`🔗 View comparison: file://${comparisonPath}`);

    } catch (error) {
        console.error('💥 Test failed:', error.message);
        console.error(error.stack);
    } finally {
        // Cleanup
        await pdfGenerator.closeBrowser();
        await previewSystem.close();
    }
}

// Create outputs directory
const fs = require('fs').promises;
async function ensureOutputsDir() {
    await fs.mkdir('./outputs', { recursive: true });
}

// Run tests
async function main() {
    await ensureOutputsDir();
    await testSimpleTemplates();
}

// Handle script execution
if (require.main === module) {
    main().catch(error => {
        console.error('Script failed:', error.message);
        process.exit(1);
    });
}

module.exports = { testSimpleTemplates };