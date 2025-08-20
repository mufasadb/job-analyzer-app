/**
 * Simple Test for Resume Templates
 * Basic test without heavy dependencies - just renders HTML with sample data
 */

const fs = require('fs').promises;
const path = require('path');

async function simpleTemplateTest() {
    console.log('🧪 Simple Template Test Starting...\n');

    try {
        // Load sample data
        console.log('📄 Loading sample data...');
        const sampleDataPath = path.join(__dirname, 'data', 'sample-data.json');
        const sampleDataContent = await fs.readFile(sampleDataPath, 'utf8');
        const sampleData = JSON.parse(sampleDataContent);
        console.log('✅ Sample data loaded successfully');
        console.log(`   Name: ${sampleData.personal.name}`);
        console.log(`   Title: ${sampleData.personal.title}`);
        console.log(`   Experience entries: ${sampleData.experience.length}`);
        console.log('');

        // Test templates
        const templates = [
            {
                name: 'Classic One Column',
                path: path.join(__dirname, 'templates', 'simple', 'classic-one-column.html')
            },
            {
                name: 'Modern Two Column', 
                path: path.join(__dirname, 'templates', 'simple', 'modern-two-column.html')
            },
            {
                name: 'White Space Emphasis',
                path: path.join(__dirname, 'templates', 'simple', 'white-space-emphasis.html')
            }
        ];

        for (const template of templates) {
            console.log(`🎨 Testing ${template.name}...`);
            
            try {
                // Read template
                const templateContent = await fs.readFile(template.path, 'utf8');
                console.log(`  ✅ Template loaded (${templateContent.length} characters)`);

                // Simple template replacement (just for testing - replace with Handlebars in production)
                let renderedHTML = templateContent;
                
                // Replace personal info
                renderedHTML = renderedHTML.replace(/\{\{personal\.name\}\}/g, sampleData.personal.name);
                renderedHTML = renderedHTML.replace(/\{\{personal\.title\}\}/g, sampleData.personal.title);
                renderedHTML = renderedHTML.replace(/\{\{personal\.email\}\}/g, sampleData.personal.email);
                renderedHTML = renderedHTML.replace(/\{\{personal\.phone\}\}/g, sampleData.personal.phone);
                renderedHTML = renderedHTML.replace(/\{\{personal\.location\}\}/g, sampleData.personal.location);
                
                // Replace summary
                renderedHTML = renderedHTML.replace(/\{\{summary\}\}/g, sampleData.summary);
                
                // Simple experience replacement (first experience entry only for demo)
                if (sampleData.experience && sampleData.experience.length > 0) {
                    const firstExp = sampleData.experience[0];
                    renderedHTML = renderedHTML.replace(/\{\{#each experience\}\}[\s\S]*?\{\{\/each\}\}/g, 
                        `<div class="experience-item">
                            <div class="job-header">
                                <div class="job-title">${firstExp.title}</div>
                                <div class="company">${firstExp.company}</div>
                                <div class="date-location">${firstExp.startDate} - ${firstExp.current ? 'Present' : firstExp.endDate}</div>
                            </div>
                            <p class="job-description">${firstExp.description}</p>
                            <ul class="achievements">
                                ${firstExp.achievements.map(ach => `<li>${ach}</li>`).join('')}
                            </ul>
                        </div>`);
                }
                
                // Simple education replacement
                if (sampleData.education && sampleData.education.length > 0) {
                    const education = sampleData.education.map(edu => 
                        `<div class="education-item">
                            <div class="degree">${edu.degree}</div>
                            <div class="school">${edu.school}</div>
                            <div class="edu-details">${edu.year}${edu.gpa ? ` • GPA: ${edu.gpa}` : ''}</div>
                        </div>`
                    ).join('');
                    
                    renderedHTML = renderedHTML.replace(/\{\{#each education\}\}[\s\S]*?\{\{\/each\}\}/g, education);
                }
                
                // Simple skills replacement
                if (sampleData.skills) {
                    if (sampleData.skills.technical) {
                        renderedHTML = renderedHTML.replace(/\{\{join skills\.technical ", "\}\}/g, 
                            sampleData.skills.technical.join(', '));
                        renderedHTML = renderedHTML.replace(/\{\{join skills\.technical " • "\}\}/g, 
                            sampleData.skills.technical.join(' • '));
                        
                        // Handle skill tags for modern template
                        const skillTags = sampleData.skills.technical.map(skill => 
                            `<span class="skill-tag">${skill}</span>`).join('');
                        renderedHTML = renderedHTML.replace(/\{\{#each skills\.technical\}\}[\s\S]*?\{\{\/each\}\}/g, skillTags);
                    }
                    
                    if (sampleData.skills.soft) {
                        renderedHTML = renderedHTML.replace(/\{\{join skills\.soft ", "\}\}/g, 
                            sampleData.skills.soft.join(', '));
                        renderedHTML = renderedHTML.replace(/\{\{join skills\.soft " • "\}\}/g, 
                            sampleData.skills.soft.join(' • '));
                    }
                    
                    if (sampleData.skills.languages) {
                        renderedHTML = renderedHTML.replace(/\{\{join skills\.languages ", "\}\}/g, 
                            sampleData.skills.languages.join(', '));
                        renderedHTML = renderedHTML.replace(/\{\{join skills\.languages " • "\}\}/g, 
                            sampleData.skills.languages.join(' • '));
                    }
                }
                
                // Clean up any remaining template syntax
                renderedHTML = renderedHTML.replace(/\{\{[^}]*\}\}/g, '');
                renderedHTML = renderedHTML.replace(/\{\{#if [^}]*\}\}/g, '');
                renderedHTML = renderedHTML.replace(/\{\{\/if\}\}/g, '');
                renderedHTML = renderedHTML.replace(/\{\{#each [^}]*\}\}/g, '');
                renderedHTML = renderedHTML.replace(/\{\{\/each\}\}/g, '');

                // Save rendered HTML
                const outputFileName = template.name.replace(/\s+/g, '-').toLowerCase() + '-rendered.html';
                const outputPath = path.join(__dirname, 'outputs', outputFileName);
                await fs.writeFile(outputPath, renderedHTML);
                
                console.log(`  ✅ HTML rendered and saved: ${outputFileName}`);
                console.log(`  📊 Output size: ${renderedHTML.length} characters`);

            } catch (error) {
                console.log(`  ❌ Error: ${error.message}`);
            }
            
            console.log('');
        }

        console.log('🎉 Simple template test completed!');
        console.log('📁 Check rendered HTML files in: ./outputs/');
        console.log('💡 To view templates: open the HTML files in your browser');
        console.log('');
        console.log('Next steps:');
        console.log('1. Install full dependencies: npm install');
        console.log('2. Run full test with PDF/Word generation: npm test');
        console.log('3. The templates are ready for Handlebars integration');

    } catch (error) {
        console.error('💥 Test failed:', error.message);
        console.error(error.stack);
    }
}

// Run the test
simpleTemplateTest().catch(error => {
    console.error('Script failed:', error.message);
    process.exit(1);
});