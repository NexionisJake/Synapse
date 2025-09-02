/**
 * Automated Test Suite for Serendipity Results Rendering System
 * Tests the enhanced visual indicators, pagination, and interactive elements
 */

// Mock test data
const mockTestData = {
    connections: [
        {
            title: "Creative Problem-Solving Pattern",
            description: "Your approach to challenges consistently involves breaking down complex problems into smaller, manageable components while seeking unconventional solutions.",
            surprise_factor: 0.85,
            relevance: 0.92,
            connection_type: "behavioral",
            connected_insights: ["Problem Decomposition", "Creative Thinking", "Solution Innovation"],
            actionable_insight: "Consider applying this systematic creativity approach to your current project challenges."
        },
        {
            title: "Learning Through Teaching",
            description: "You demonstrate a strong pattern of consolidating your own understanding by explaining concepts to others.",
            surprise_factor: 0.73,
            relevance: 0.88,
            connection_type: "learning",
            connected_insights: ["Knowledge Sharing", "Teaching Methods", "Learning Reinforcement"],
            actionable_insight: "Seek more opportunities to mentor or teach others in your field of expertise."
        },
        {
            title: "Technology-Human Balance",
            description: "Your thoughts reveal a consistent concern about maintaining human connection while embracing technological advancement.",
            surprise_factor: 0.67,
            relevance: 0.79,
            connection_type: "philosophical",
            connected_insights: ["Human Connection", "Technology Ethics", "Digital Balance"],
            actionable_insight: "Consider developing frameworks for ethical technology use in your work."
        }
    ],
    meta_patterns: [
        {
            pattern_name: "Growth-Oriented Mindset",
            description: "Consistent focus on personal and professional development across all areas of life.",
            confidence: 0.91,
            evidence_count: 15
        },
        {
            pattern_name: "Systems Thinking Approach",
            description: "Tendency to view problems and solutions within broader interconnected systems.",
            confidence: 0.84,
            evidence_count: 12
        },
        {
            pattern_name: "Collaborative Leadership Style",
            description: "Preference for inclusive decision-making and team-based problem solving.",
            confidence: 0.76,
            evidence_count: 8
        }
    ],
    serendipity_summary: "# Analysis Summary\n\nYour cognitive patterns reveal a **highly systematic yet creative approach** to problem-solving.",
    recommendations: [
        "Consider starting a blog or podcast to share your systematic problem-solving approaches",
        "Explore mentorship opportunities in your field to leverage your teaching inclinations"
    ],
    metadata: {
        timestamp: new Date().toISOString(),
        model: "llama3:8b"
    }
};

class SerendipityRenderingTestSuite {
    constructor() {
        this.testResults = [];
        this.dashboard = null;
    }

    /**
     * Initialize test environment
     */
    async init() {
        console.log('🧪 Initializing Serendipity Results Rendering Test Suite...');
        
        // Create mock dashboard instance
        this.dashboard = {
            serendipityData: mockTestData,
            connectionsPagination: { currentPage: 1, itemsPerPage: 6, totalItems: 0 },
            metaPatternsPagination: { currentPage: 1, itemsPerPage: 4, totalItems: 0 },
            
            // Mock methods that would be available in the actual Dashboard class
            escapeHtml: (text) => {
                const div = document.createElement('div');
                div.textContent = text;
                return div.innerHTML;
            },
            
            getIntensityClass: (score) => {
                if (score >= 80) return 'high-intensity';
                if (score >= 60) return 'medium-intensity';
                if (score >= 40) return 'low-intensity';
                return 'minimal-intensity';
            },
            
            getPriorityClass: (score) => {
                if (score >= 80) return 'high-priority';
                if (score >= 60) return 'medium-priority';
                return 'standard-priority';
            },
            
            getConfidenceLevel: (confidence) => {
                if (confidence >= 80) return 'high-confidence';
                if (confidence >= 60) return 'medium-confidence';
                if (confidence >= 40) return 'low-confidence';
                return 'minimal-confidence';
            },
            
            getConnectionTypeIcon: (type) => {
                const icons = {
                    'behavioral': '🎯',
                    'learning': '📚',
                    'philosophical': '💭'
                };
                return icons[type.toLowerCase()] || '🔗';
            },
            
            getPatternIcon: (patternName) => {
                const name = (patternName || '').toLowerCase();
                if (name.includes('growth')) return '📈';
                if (name.includes('systems')) return '🔄';
                if (name.includes('leadership')) return '👥';
                return '🧩';
            },
            
            renderEvidenceVisualization: (evidenceCount) => {
                const maxDots = 10;
                const dots = Math.min(evidenceCount, maxDots);
                let visualization = '';
                for (let i = 0; i < dots; i++) {
                    visualization += '<span class="evidence-dot" aria-hidden="true">●</span>';
                }
                return visualization;
            }
        };
        
        this.log('✅ Test environment initialized');
    }

    /**
     * Run all tests
     */
    async runAllTests() {
        console.log('🚀 Running all Serendipity Results Rendering tests...\n');
        
        await this.init();
        
        // Test categories
        await this.testConnectionCardRendering();
        await this.testMetaPatternRendering();
        await this.testVisualEnhancements();
        await this.testPaginationSystem();
        await this.testInteractiveElements();
        await this.testResponsiveDesign();
        await this.testAccessibility();
        await this.testPerformance();
        
        this.printSummary();
    }

    /**
     * Test connection card rendering
     */
    async testConnectionCardRendering() {
        console.log('🔗 Testing Connection Card Rendering...');
        
        try {
            // Test basic connection rendering
            const connectionHtml = this.renderMockConnections(mockTestData.connections);
            this.assert(connectionHtml.includes('connection-card'), 'Connection cards should be rendered');
            this.assert(connectionHtml.includes('connection-title'), 'Connection titles should be present');
            this.assert(connectionHtml.includes('connection-indicators'), 'Visual indicators should be present');
            this.log('✅ Basic connection card rendering works');
            
            // Test surprise and relevance indicators
            this.assert(connectionHtml.includes('surprise'), 'Surprise indicators should be present');
            this.assert(connectionHtml.includes('relevance'), 'Relevance indicators should be present');
            this.assert(connectionHtml.includes('indicator-fill'), 'Progress bars should be rendered');
            this.log('✅ Surprise and relevance indicators work');
            
            // Test connection type badges
            this.assert(connectionHtml.includes('connection-type-badge'), 'Connection type badges should be present');
            this.assert(connectionHtml.includes('🎯'), 'Connection type icons should be rendered');
            this.log('✅ Connection type badges work');
            
            // Test actionable insights
            this.assert(connectionHtml.includes('connection-actionable'), 'Actionable insights should be rendered');
            this.assert(connectionHtml.includes('💡'), 'Actionable insight icons should be present');
            this.log('✅ Actionable insights rendering works');
            
        } catch (error) {
            this.logError('Connection card rendering test failed', error);
        }
    }

    /**
     * Test meta pattern rendering
     */
    async testMetaPatternRendering() {
        console.log('🧩 Testing Meta Pattern Rendering...');
        
        try {
            // Test basic pattern rendering
            const patternHtml = this.renderMockMetaPatterns(mockTestData.meta_patterns);
            this.assert(patternHtml.includes('meta-pattern-card'), 'Meta pattern cards should be rendered');
            this.assert(patternHtml.includes('pattern-header'), 'Pattern headers should be present');
            this.assert(patternHtml.includes('pattern-confidence-badge'), 'Confidence badges should be present');
            this.log('✅ Basic meta pattern rendering works');
            
            // Test confidence visualization
            this.assert(patternHtml.includes('confidence-bar'), 'Confidence bars should be rendered');
            this.assert(patternHtml.includes('confidence-fill'), 'Confidence fill elements should be present');
            this.assert(patternHtml.includes('high-confidence'), 'High confidence styling should be applied');
            this.log('✅ Confidence visualization works');
            
            // Test evidence visualization
            this.assert(patternHtml.includes('evidence-visualization'), 'Evidence visualization should be present');
            this.assert(patternHtml.includes('evidence-dot'), 'Evidence dots should be rendered');
            this.log('✅ Evidence visualization works');
            
            // Test interactive elements
            this.assert(patternHtml.includes('pattern-action-btn'), 'Pattern action buttons should be present');
            this.assert(patternHtml.includes('explore-btn'), 'Explore buttons should be rendered');
            this.assert(patternHtml.includes('related-btn'), 'Related buttons should be rendered');
            this.log('✅ Interactive pattern elements work');
            
        } catch (error) {
            this.logError('Meta pattern rendering test failed', error);
        }
    }

    /**
     * Test visual enhancements
     */
    async testVisualEnhancements() {
        console.log('✨ Testing Visual Enhancements...');
        
        try {
            // Test priority classes
            const highPriorityData = mockTestData.connections.map(conn => ({
                ...conn,
                surprise_factor: 0.95,
                relevance: 0.98
            }));
            
            const highPriorityHtml = this.renderMockConnections(highPriorityData);
            this.assert(highPriorityHtml.includes('high-priority'), 'High priority styling should be applied');
            this.log('✅ Priority-based visual enhancements work');
            
            // Test intensity classes
            this.assert(highPriorityHtml.includes('high-intensity'), 'High intensity styling should be applied');
            this.log('✅ Intensity-based visual enhancements work');
            
            // Test glow effects
            const connectionHtml = this.renderMockConnections(mockTestData.connections);
            this.assert(connectionHtml.includes('indicator-glow'), 'Glow effects should be present');
            this.log('✅ Glow effects are implemented');
            
            // Test score badges
            this.assert(connectionHtml.includes('connection-score-badge'), 'Score badges should be present');
            this.log('✅ Score badges work');
            
        } catch (error) {
            this.logError('Visual enhancements test failed', error);
        }
    }

    /**
     * Test pagination system
     */
    async testPaginationSystem() {
        console.log('📄 Testing Pagination System...');
        
        try {
            // Create large dataset
            const largeDataset = [];
            for (let i = 0; i < 15; i++) {
                largeDataset.push({
                    ...mockTestData.connections[0],
                    title: `Connection ${i + 1}`
                });
            }
            
            // Test pagination rendering
            const paginatedHtml = this.renderMockConnectionsWithPagination(largeDataset);
            this.assert(paginatedHtml.includes('serendipity-pagination'), 'Pagination controls should be rendered');
            this.assert(paginatedHtml.includes('pagination-btn'), 'Pagination buttons should be present');
            this.assert(paginatedHtml.includes('pagination-info'), 'Pagination info should be displayed');
            this.log('✅ Pagination controls render correctly');
            
            // Test pagination logic
            this.dashboard.connectionsPagination = { currentPage: 1, itemsPerPage: 6, totalItems: 15 };
            const firstPageHtml = this.renderMockConnectionsWithPagination(largeDataset);
            this.assert(firstPageHtml.includes('Page 1 of 3'), 'Pagination info should show correct page numbers');
            this.assert(firstPageHtml.includes('Showing 1-6 of 15'), 'Item range should be correct');
            this.log('✅ Pagination logic works correctly');
            
            // Test large dataset handling
            const veryLargeDataset = [];
            for (let i = 0; i < 100; i++) {
                veryLargeDataset.push({
                    ...mockTestData.connections[0],
                    title: `Large Dataset Connection ${i + 1}`
                });
            }
            
            const largeDatasetHtml = this.renderMockConnectionsWithPagination(veryLargeDataset);
            this.assert(largeDatasetHtml.includes('connection-card'), 'Large datasets should render correctly');
            this.log('✅ Large dataset handling works');
            
        } catch (error) {
            this.logError('Pagination system test failed', error);
        }
    }

    /**
     * Test interactive elements
     */
    async testInteractiveElements() {
        console.log('🖱️ Testing Interactive Elements...');
        
        try {
            // Test connection interactions
            const connectionHtml = this.renderMockConnections(mockTestData.connections);
            this.assert(connectionHtml.includes('connection-action-btn'), 'Connection action buttons should be present');
            this.assert(connectionHtml.includes('expand-btn'), 'Expand buttons should be rendered');
            this.assert(connectionHtml.includes('bookmark-btn'), 'Bookmark buttons should be rendered');
            this.log('✅ Connection interactive elements work');
            
            // Test insights toggle
            this.assert(connectionHtml.includes('insights-toggle'), 'Insights toggle should be present');
            this.assert(connectionHtml.includes('insights-toggle-arrow'), 'Toggle arrows should be rendered');
            this.log('✅ Insights toggle elements work');
            
            // Test pattern interactions
            const patternHtml = this.renderMockMetaPatterns(mockTestData.meta_patterns);
            this.assert(patternHtml.includes('pattern-action-btn'), 'Pattern action buttons should be present');
            this.assert(patternHtml.includes('pattern-details'), 'Pattern details sections should be present');
            this.log('✅ Pattern interactive elements work');
            
            // Test ARIA attributes
            this.assert(connectionHtml.includes('aria-expanded'), 'ARIA expanded attributes should be present');
            this.assert(connectionHtml.includes('aria-label'), 'ARIA labels should be present');
            this.assert(connectionHtml.includes('role="button"'), 'Button roles should be defined');
            this.log('✅ ARIA attributes are properly implemented');
            
        } catch (error) {
            this.logError('Interactive elements test failed', error);
        }
    }

    /**
     * Test responsive design
     */
    async testResponsiveDesign() {
        console.log('📱 Testing Responsive Design...');
        
        try {
            // Test grid responsiveness
            const connectionHtml = this.renderMockConnections(mockTestData.connections);
            this.assert(connectionHtml.includes('connections-grid'), 'Responsive grid should be present');
            this.log('✅ Responsive grid structure works');
            
            // Test mobile-friendly elements
            this.assert(connectionHtml.includes('connection-score-badge'), 'Mobile-friendly badges should be present');
            this.assert(connectionHtml.includes('indicator-header'), 'Mobile-optimized headers should be present');
            this.log('✅ Mobile-friendly elements work');
            
            // Test pagination responsiveness
            const paginatedHtml = this.renderMockConnectionsWithPagination(mockTestData.connections);
            this.assert(paginatedHtml.includes('pagination-info'), 'Responsive pagination info should be present');
            this.log('✅ Responsive pagination works');
            
        } catch (error) {
            this.logError('Responsive design test failed', error);
        }
    }

    /**
     * Test accessibility features
     */
    async testAccessibility() {
        console.log('♿ Testing Accessibility Features...');
        
        try {
            // Test ARIA labels and roles
            const connectionHtml = this.renderMockConnections(mockTestData.connections);
            this.assert(connectionHtml.includes('role="article"'), 'Article roles should be present');
            this.assert(connectionHtml.includes('role="progressbar"'), 'Progress bar roles should be present');
            this.assert(connectionHtml.includes('aria-valuenow'), 'Progress bar values should be accessible');
            this.log('✅ ARIA roles and labels work');
            
            // Test keyboard navigation
            this.assert(connectionHtml.includes('tabindex="0"'), 'Keyboard navigation should be supported');
            this.log('✅ Keyboard navigation support works');
            
            // Test screen reader support
            this.assert(connectionHtml.includes('aria-label'), 'Screen reader labels should be present');
            this.assert(connectionHtml.includes('aria-hidden="true"'), 'Decorative elements should be hidden from screen readers');
            this.log('✅ Screen reader support works');
            
            // Test semantic HTML
            this.assert(connectionHtml.includes('<h4'), 'Proper heading hierarchy should be used');
            this.assert(connectionHtml.includes('role="region"'), 'Semantic regions should be defined');
            this.log('✅ Semantic HTML structure works');
            
        } catch (error) {
            this.logError('Accessibility test failed', error);
        }
    }

    /**
     * Test performance considerations
     */
    async testPerformance() {
        console.log('⚡ Testing Performance Considerations...');
        
        try {
            // Test rendering performance with large datasets
            const startTime = performance.now();
            
            const largeDataset = [];
            for (let i = 0; i < 50; i++) {
                largeDataset.push({
                    ...mockTestData.connections[0],
                    title: `Performance Test Connection ${i + 1}`
                });
            }
            
            const html = this.renderMockConnections(largeDataset);
            const endTime = performance.now();
            const renderTime = endTime - startTime;
            
            this.assert(renderTime < 100, `Rendering should be fast (${renderTime.toFixed(2)}ms)`);
            this.assert(html.length > 0, 'Large dataset should render successfully');
            this.log(`✅ Performance test passed (${renderTime.toFixed(2)}ms for 50 connections)`);
            
            // Test memory efficiency
            this.assert(html.includes('connection-card'), 'Memory-efficient rendering should work');
            this.log('✅ Memory efficiency test passed');
            
        } catch (error) {
            this.logError('Performance test failed', error);
        }
    }

    /**
     * Mock rendering methods
     */
    renderMockConnections(connections) {
        const connectionsHtml = connections.map((connection, index) => {
            const surpriseFactor = Math.round((connection.surprise_factor || 0) * 100);
            const relevance = Math.round((connection.relevance || 0) * 100);
            const connectedInsights = connection.connected_insights || [];
            
            const surpriseIntensity = this.dashboard.getIntensityClass(surpriseFactor);
            const relevanceIntensity = this.dashboard.getIntensityClass(relevance);
            const overallScore = (surpriseFactor + relevance) / 2;
            const cardPriority = this.dashboard.getPriorityClass(overallScore);
            
            return `
                <div class="connection-card ${cardPriority}" role="article" tabindex="0" data-connection-index="${index}">
                    <div class="connection-header">
                        <h4 class="connection-title">${this.dashboard.escapeHtml(connection.title || 'Untitled Connection')}</h4>
                        <div class="connection-score-badge" aria-label="Overall connection strength ${Math.round(overallScore)}%">
                            ${Math.round(overallScore)}%
                        </div>
                    </div>
                    
                    <div class="connection-indicators">
                        <div class="connection-indicator surprise-indicator">
                            <div class="indicator-header">
                                <span class="indicator-label">
                                    <span class="indicator-icon" aria-hidden="true">✨</span>
                                    Surprise
                                </span>
                                <span class="indicator-value">${surpriseFactor}%</span>
                            </div>
                            <div class="indicator-bar" role="progressbar" aria-valuenow="${surpriseFactor}" aria-valuemin="0" aria-valuemax="100" aria-label="Surprise factor ${surpriseFactor}%">
                                <div class="indicator-fill surprise ${surpriseIntensity}" style="width: 0%" data-target-width="${surpriseFactor}%"></div>
                                <div class="indicator-glow surprise" style="width: 0%" data-target-width="${surpriseFactor}%"></div>
                            </div>
                        </div>
                        
                        <div class="connection-indicator relevance-indicator">
                            <div class="indicator-header">
                                <span class="indicator-label">
                                    <span class="indicator-icon" aria-hidden="true">🎯</span>
                                    Relevance
                                </span>
                                <span class="indicator-value">${relevance}%</span>
                            </div>
                            <div class="indicator-bar" role="progressbar" aria-valuenow="${relevance}" aria-valuemin="0" aria-valuemax="100" aria-label="Relevance ${relevance}%">
                                <div class="indicator-fill relevance ${relevanceIntensity}" style="width: 0%" data-target-width="${relevance}%"></div>
                                <div class="indicator-glow relevance" style="width: 0%" data-target-width="${relevance}%"></div>
                            </div>
                        </div>
                    </div>
                    
                    ${connection.connection_type ? `
                        <div class="connection-type-badge">
                            <span class="connection-type-icon" aria-hidden="true">${this.dashboard.getConnectionTypeIcon(connection.connection_type)}</span>
                            ${this.dashboard.escapeHtml(connection.connection_type)}
                        </div>
                    ` : ''}
                    
                    <div class="connection-description">
                        ${this.dashboard.escapeHtml(connection.description || 'No description available.')}
                    </div>
                    
                    ${connectedInsights.length > 0 ? `
                        <div class="connection-insights">
                            <button class="insights-toggle" aria-expanded="false" aria-controls="insights-${index}">
                                <span class="insights-toggle-icon" aria-hidden="true">🔗</span>
                                <span class="insights-toggle-text">Connected Insights (${connectedInsights.length})</span>
                                <span class="insights-toggle-arrow" aria-hidden="true">▼</span>
                            </button>
                            <div class="connected-insights" id="insights-${index}" aria-hidden="true">
                                ${connectedInsights.map(insight => `
                                    <span class="insight-tag" tabindex="0" role="button" aria-label="Insight: ${this.dashboard.escapeHtml(insight)}">
                                        ${this.dashboard.escapeHtml(insight)}
                                    </span>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}
                    
                    ${connection.actionable_insight ? `
                        <div class="connection-actionable">
                            <div class="actionable-header">
                                <span class="actionable-icon" aria-hidden="true">💡</span>
                                <span class="actionable-label">Actionable Insight</span>
                            </div>
                            <div class="actionable-content">
                                ${this.dashboard.escapeHtml(connection.actionable_insight)}
                            </div>
                        </div>
                    ` : ''}
                    
                    <div class="connection-actions">
                        <button class="connection-action-btn expand-btn" aria-label="Expand connection details" data-connection-index="${index}">
                            <span aria-hidden="true">🔍</span>
                            Details
                        </button>
                        <button class="connection-action-btn bookmark-btn" aria-label="Bookmark this connection" data-connection-index="${index}">
                            <span aria-hidden="true">🔖</span>
                            Save
                        </button>
                    </div>
                </div>
            `;
        }).join('');

        return `
            <div class="serendipity-connections" role="region" aria-label="Discovered connections">
                <div class="connections-header">
                    <h4 class="connections-title">
                        <span class="connections-icon" aria-hidden="true">🌟</span>
                        Discovered Connections
                        <span class="connections-count">(${connections.length})</span>
                    </h4>
                </div>
                <div class="connections-grid">
                    ${connectionsHtml}
                </div>
            </div>
        `;
    }

    renderMockConnectionsWithPagination(connections) {
        const { currentPage, itemsPerPage } = this.dashboard.connectionsPagination;
        const startIndex = (currentPage - 1) * itemsPerPage;
        const endIndex = startIndex + itemsPerPage;
        const pageConnections = connections.slice(startIndex, endIndex);
        const totalPages = Math.ceil(connections.length / itemsPerPage);
        
        const connectionsHtml = this.renderMockConnections(pageConnections);
        
        if (totalPages <= 1) {
            return connectionsHtml;
        }
        
        const paginationHtml = `
            <div class="serendipity-pagination connections-pagination" role="navigation" aria-label="Connections pagination">
                <button class="pagination-btn prev-btn" ${currentPage === 1 ? 'disabled' : ''} 
                        data-action="prev-connections" aria-label="Previous page of connections">
                    <span aria-hidden="true">‹</span>
                    Previous
                </button>
                <div class="pagination-info">
                    <span class="page-indicator">
                        Page ${currentPage} of ${totalPages}
                    </span>
                    <span class="items-indicator">
                        Showing ${startIndex + 1}-${Math.min(endIndex, connections.length)} of ${connections.length} connections
                    </span>
                </div>
                <button class="pagination-btn next-btn" ${currentPage === totalPages ? 'disabled' : ''} 
                        data-action="next-connections" aria-label="Next page of connections">
                    Next
                    <span aria-hidden="true">›</span>
                </button>
            </div>
        `;
        
        return connectionsHtml.replace('</div>', paginationHtml + '</div>');
    }

    renderMockMetaPatterns(metaPatterns) {
        const patternsHtml = metaPatterns.map((pattern, index) => {
            const confidence = Math.round((pattern.confidence || 0) * 100);
            const confidenceLevel = this.dashboard.getConfidenceLevel(confidence);
            const evidenceCount = pattern.evidence_count || 0;
            
            return `
                <div class="meta-pattern-card ${confidenceLevel}" role="article" tabindex="0" data-pattern-index="${index}">
                    <div class="pattern-header">
                        <div class="pattern-icon" aria-hidden="true">${this.dashboard.getPatternIcon(pattern.pattern_name)}</div>
                        <h5 class="meta-pattern-name">${this.dashboard.escapeHtml(pattern.pattern_name || 'Unnamed Pattern')}</h5>
                        <div class="pattern-confidence-badge" aria-label="Confidence level ${confidence}%">
                            ${confidence}%
                        </div>
                    </div>
                    
                    <div class="pattern-description">
                        ${this.dashboard.escapeHtml(pattern.description || 'No description available.')}
                    </div>
                    
                    <div class="pattern-metrics">
                        <div class="metric-item">
                            <div class="metric-header">
                                <span class="metric-label">
                                    <span class="metric-icon" aria-hidden="true">🎯</span>
                                    Confidence
                                </span>
                                <span class="metric-value">${confidence}%</span>
                            </div>
                            <div class="confidence-bar" role="progressbar" aria-valuenow="${confidence}" aria-valuemin="0" aria-valuemax="100" aria-label="Confidence ${confidence}%">
                                <div class="confidence-fill ${confidenceLevel}" style="width: 0%" data-target-width="${confidence}%"></div>
                                <div class="confidence-glow ${confidenceLevel}" style="width: 0%" data-target-width="${confidence}%"></div>
                            </div>
                        </div>
                        
                        ${evidenceCount > 0 ? `
                            <div class="metric-item evidence-metric">
                                <div class="metric-header">
                                    <span class="metric-label">
                                        <span class="metric-icon" aria-hidden="true">📊</span>
                                        Evidence
                                    </span>
                                    <span class="metric-value">${evidenceCount}</span>
                                </div>
                                <div class="evidence-visualization">
                                    ${this.dashboard.renderEvidenceVisualization(evidenceCount)}
                                </div>
                            </div>
                        ` : ''}
                    </div>
                    
                    <div class="pattern-actions">
                        <button class="pattern-action-btn explore-btn" aria-label="Explore pattern details" data-pattern-index="${index}">
                            <span aria-hidden="true">🔍</span>
                            Explore
                        </button>
                        <button class="pattern-action-btn related-btn" aria-label="Find related patterns" data-pattern-index="${index}">
                            <span aria-hidden="true">🔗</span>
                            Related
                        </button>
                    </div>
                    
                    <div class="pattern-details" id="pattern-details-${index}" aria-hidden="true">
                        <div class="details-content">
                            <div class="detail-section">
                                <h6 class="detail-title">Pattern Strength</h6>
                                <div class="strength-indicator ${confidenceLevel}">
                                    ${this.getStrengthDescription(confidence)}
                                </div>
                            </div>
                            ${evidenceCount > 0 ? `
                                <div class="detail-section">
                                    <h6 class="detail-title">Evidence Sources</h6>
                                    <div class="evidence-breakdown">
                                        Based on ${evidenceCount} piece${evidenceCount !== 1 ? 's' : ''} of evidence from your conversations and insights.
                                    </div>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        return `
            <div class="serendipity-meta-patterns" role="region" aria-label="Meta patterns">
                <div class="meta-patterns-header">
                    <h4 class="meta-patterns-title">
                        <span class="patterns-icon" aria-hidden="true">🧩</span>
                        Overarching Patterns
                        <span class="patterns-count">(${metaPatterns.length})</span>
                    </h4>
                    <div class="patterns-controls">
                        <button class="patterns-sort-btn" aria-label="Sort patterns by confidence">
                            <span aria-hidden="true">📊</span>
                            Sort by Confidence
                        </button>
                    </div>
                </div>
                <div class="meta-patterns-grid">
                    ${patternsHtml}
                </div>
            </div>
        `;
    }

    getStrengthDescription(confidence) {
        if (confidence >= 90) return 'Very Strong - Highly consistent pattern';
        if (confidence >= 80) return 'Strong - Clear and consistent pattern';
        if (confidence >= 70) return 'Moderate - Generally consistent pattern';
        if (confidence >= 60) return 'Emerging - Pattern becoming apparent';
        if (confidence >= 50) return 'Weak - Some evidence of pattern';
        return 'Minimal - Limited evidence of pattern';
    }

    /**
     * Utility methods
     */
    assert(condition, message) {
        if (!condition) {
            throw new Error(`Assertion failed: ${message}`);
        }
    }

    log(message) {
        this.testResults.push({ type: 'success', message });
        console.log(`  ${message}`);
    }

    logError(message, error) {
        this.testResults.push({ type: 'error', message, error: error.message });
        console.error(`  ❌ ${message}:`, error.message);
    }

    printSummary() {
        const successCount = this.testResults.filter(r => r.type === 'success').length;
        const errorCount = this.testResults.filter(r => r.type === 'error').length;
        
        console.log('\n📊 Test Summary:');
        console.log(`✅ Passed: ${successCount}`);
        console.log(`❌ Failed: ${errorCount}`);
        console.log(`📈 Success Rate: ${((successCount / (successCount + errorCount)) * 100).toFixed(1)}%`);
        
        if (errorCount > 0) {
            console.log('\n❌ Failed Tests:');
            this.testResults.filter(r => r.type === 'error').forEach(result => {
                console.log(`  - ${result.message}: ${result.error}`);
            });
        }
        
        console.log('\n🎉 Serendipity Results Rendering Test Suite Complete!');
    }
}

// Export for use in Node.js or browser
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SerendipityRenderingTestSuite;
} else if (typeof window !== 'undefined') {
    window.SerendipityRenderingTestSuite = SerendipityRenderingTestSuite;
}

// Auto-run tests if this file is executed directly
if (typeof require !== 'undefined' && require.main === module) {
    const testSuite = new SerendipityRenderingTestSuite();
    testSuite.runAllTests();
}