/**
 * Browser Compatibility Test Suite for Serendipity Analysis
 * Tests cross-browser compatibility, responsive design, and accessibility
 */

class BrowserCompatibilityTester {
    constructor() {
        this.results = {
            core: [],
            css: [],
            responsive: [],
            accessibility: [],
            performance: []
        };
        this.dashboard = null;
    }

    async runAllTests() {
        console.log('🚀 Starting Browser Compatibility Tests...');
        
        this.displayBrowserInfo();
        await this.testCoreFeatures();
        await this.testCSSFeatures();
        await this.testResponsiveDesign();
        await this.testAccessibilityFeatures();
        await this.testPerformanceFeatures();
        
        this.displayResults();
        console.log('✅ Browser Compatibility Tests Complete');
    }

    displayBrowserInfo() {
        const nav = navigator;
        const browserInfo = {
            userAgent: nav.userAgent,
            platform: nav.platform,
            language: nav.language,
            cookieEnabled: nav.cookieEnabled,
            onLine: nav.onLine,
            screenResolution: `${screen.width}x${screen.height}`,
            colorDepth: screen.colorDepth,
            pixelRatio: window.devicePixelRatio || 1
        };

        const browserDetails = document.getElementById('browser-details');
        browserDetails.innerHTML = `
            <div class="feature-grid">
                <div><strong>User Agent:</strong> ${browserInfo.userAgent}</div>
                <div><strong>Platform:</strong> ${browserInfo.platform}</div>
                <div><strong>Language:</strong> ${browserInfo.language}</div>
                <div><strong>Screen:</strong> ${browserInfo.screenResolution}</div>
                <div><strong>Color Depth:</strong> ${browserInfo.colorDepth}</div>
                <div><strong>Pixel Ratio:</strong> ${browserInfo.pixelRatio}</div>
                <div><strong>Cookies:</strong> ${browserInfo.cookieEnabled ? 'Enabled' : 'Disabled'}</div>
                <div><strong>Online:</strong> ${browserInfo.onLine ? 'Yes' : 'No'}</div>
            </div>
        `;
    }

    async testCoreFeatures() {
        console.log('Testing core JavaScript features...');

        const tests = [
            { name: 'ES6 Arrow Functions', test: () => (() => true)() },
            { name: 'ES6 Template Literals', test: () => `test` === 'test' },
            { name: 'ES6 Destructuring', test: () => { const {a} = {a: 1}; return a === 1; } },
            { name: 'ES6 Spread Operator', test: () => [...[1, 2]].length === 2 },
            { name: 'ES6 Classes', test: () => { class Test {} return new Test() instanceof Test; } },
            { name: 'Promises', test: () => typeof Promise !== 'undefined' },
            { name: 'Async/Await', test: () => { try { eval('async function test() { await 1; }'); return true; } catch(e) { return false; } } },
            { name: 'Fetch API', test: () => typeof fetch !== 'undefined' },
            { name: 'Local Storage', test: () => typeof localStorage !== 'undefined' },
            { name: 'Session Storage', test: () => typeof sessionStorage !== 'undefined' },
            { name: 'JSON Support', test: () => typeof JSON !== 'undefined' },
            { name: 'Array.from', test: () => typeof Array.from !== 'undefined' },
            { name: 'Array.includes', test: () => typeof Array.prototype.includes !== 'undefined' },
            { name: 'Object.assign', test: () => typeof Object.assign !== 'undefined' },
            { name: 'Map/Set', test: () => typeof Map !== 'undefined' && typeof Set !== 'undefined' }
        ];

        for (const test of tests) {
            try {
                const result = test.test();
                this.results.core.push({
                    name: test.name,
                    status: result ? 'pass' : 'fail',
                    message: result ? 'Supported' : 'Not supported'
                });
            } catch (error) {
                this.results.core.push({
                    name: test.name,
                    status: 'fail',
                    message: `Error: ${error.message}`
                });
            }
        }
    }

    async testCSSFeatures() {
        console.log('Testing CSS feature support...');

        const testElement = document.createElement('div');
        document.body.appendChild(testElement);

        const cssTests = [
            { name: 'CSS Grid', property: 'display', value: 'grid' },
            { name: 'CSS Flexbox', property: 'display', value: 'flex' },
            { name: 'CSS Variables', property: '--test-var', value: 'test' },
            { name: 'CSS Transforms', property: 'transform', value: 'translateX(10px)' },
            { name: 'CSS Transitions', property: 'transition', value: 'all 0.3s ease' },
            { name: 'CSS Animations', property: 'animation', value: 'test 1s ease' },
            { name: 'CSS Border Radius', property: 'borderRadius', value: '10px' },
            { name: 'CSS Box Shadow', property: 'boxShadow', value: '0 2px 4px rgba(0,0,0,0.1)' },
            { name: 'CSS Gradients', property: 'background', value: 'linear-gradient(to right, red, blue)' },
            { name: 'CSS Media Queries', test: () => window.matchMedia('(min-width: 1px)').matches }
        ];

        for (const test of cssTests) {
            try {
                if (test.test) {
                    const result = test.test();
                    this.results.css.push({
                        name: test.name,
                        status: result ? 'pass' : 'fail',
                        message: result ? 'Supported' : 'Not supported'
                    });
                } else {
                    testElement.style[test.property] = test.value;
                    const supported = testElement.style[test.property] !== '';
                    this.results.css.push({
                        name: test.name,
                        status: supported ? 'pass' : 'fail',
                        message: supported ? 'Supported' : 'Not supported'
                    });
                }
            } catch (error) {
                this.results.css.push({
                    name: test.name,
                    status: 'fail',
                    message: `Error: ${error.message}`
                });
            }
        }

        document.body.removeChild(testElement);
    }

    async testResponsiveDesign() {
        console.log('Testing responsive design features...');

        const viewportTests = [
            { name: 'Viewport Meta Tag', test: () => {
                const viewport = document.querySelector('meta[name="viewport"]');
                return viewport && viewport.content.includes('width=device-width');
            }},
            { name: 'Media Query Support', test: () => window.matchMedia('(max-width: 768px)').matches !== undefined },
            { name: 'Touch Events', test: () => 'ontouchstart' in window || navigator.maxTouchPoints > 0 },
            { name: 'Orientation Change', test: () => 'orientation' in screen || 'orientation' in window },
            { name: 'Device Pixel Ratio', test: () => window.devicePixelRatio !== undefined }
        ];

        // Test different viewport sizes
        const originalWidth = window.innerWidth;
        const originalHeight = window.innerHeight;

        for (const test of viewportTests) {
            try {
                const result = test.test();
                this.results.responsive.push({
                    name: test.name,
                    status: result ? 'pass' : 'fail',
                    message: result ? 'Supported' : 'Not supported'
                });
            } catch (error) {
                this.results.responsive.push({
                    name: test.name,
                    status: 'fail',
                    message: `Error: ${error.message}`
                });
            }
        }

        // Test responsive breakpoints
        const breakpoints = [
            { name: 'Mobile (320px)', width: 320 },
            { name: 'Tablet (768px)', width: 768 },
            { name: 'Desktop (1024px)', width: 1024 },
            { name: 'Large Desktop (1440px)', width: 1440 }
        ];

        for (const breakpoint of breakpoints) {
            const mediaQuery = window.matchMedia(`(min-width: ${breakpoint.width}px)`);
            this.results.responsive.push({
                name: `${breakpoint.name} Breakpoint`,
                status: 'pass',
                message: `Current: ${window.innerWidth}px, Matches: ${mediaQuery.matches}`
            });
        }
    }

    async testAccessibilityFeatures() {
        console.log('Testing accessibility features...');

        const accessibilityTests = [
            { name: 'ARIA Support', test: () => {
                const testEl = document.createElement('div');
                testEl.setAttribute('aria-label', 'test');
                return testEl.getAttribute('aria-label') === 'test';
            }},
            { name: 'Focus Management', test: () => {
                const button = document.getElementById('discover-connections-btn');
                return button && typeof button.focus === 'function';
            }},
            { name: 'Keyboard Navigation', test: () => {
                return 'KeyboardEvent' in window;
            }},
            { name: 'Screen Reader Support', test: () => {
                const liveRegion = document.querySelector('[aria-live]');
                return liveRegion !== null;
            }},
            { name: 'High Contrast Mode', test: () => {
                if (window.matchMedia) {
                    return window.matchMedia('(prefers-contrast: high)').matches !== undefined;
                }
                return false;
            }},
            { name: 'Reduced Motion', test: () => {
                if (window.matchMedia) {
                    return window.matchMedia('(prefers-reduced-motion: reduce)').matches !== undefined;
                }
                return false;
            }},
            { name: 'Color Scheme Preference', test: () => {
                if (window.matchMedia) {
                    return window.matchMedia('(prefers-color-scheme: dark)').matches !== undefined;
                }
                return false;
            }}
        ];

        for (const test of accessibilityTests) {
            try {
                const result = test.test();
                this.results.accessibility.push({
                    name: test.name,
                    status: result ? 'pass' : 'warn',
                    message: result ? 'Supported' : 'Limited support'
                });
            } catch (error) {
                this.results.accessibility.push({
                    name: test.name,
                    status: 'fail',
                    message: `Error: ${error.message}`
                });
            }
        }

        // Test actual serendipity components for accessibility
        this.testSerendipityAccessibility();
    }

    testSerendipityAccessibility() {
        const button = document.getElementById('discover-connections-btn');
        const status = document.getElementById('serendipity-status');
        const results = document.getElementById('serendipity-results');

        const componentTests = [
            { name: 'Button ARIA Attributes', test: () => button && button.hasAttribute('aria-describedby') },
            { name: 'Status Live Region', test: () => status && status.getAttribute('aria-live') === 'polite' },
            { name: 'Results Region Role', test: () => results && results.hasAttribute('role') },
            { name: 'Button Type Attribute', test: () => button && button.getAttribute('type') === 'button' },
            { name: 'Semantic HTML Structure', test: () => {
                const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
                return headings.length > 0;
            }}
        ];

        for (const test of componentTests) {
            try {
                const result = test.test();
                this.results.accessibility.push({
                    name: `Serendipity ${test.name}`,
                    status: result ? 'pass' : 'fail',
                    message: result ? 'Properly implemented' : 'Missing or incorrect'
                });
            } catch (error) {
                this.results.accessibility.push({
                    name: `Serendipity ${test.name}`,
                    status: 'fail',
                    message: `Error: ${error.message}`
                });
            }
        }
    }

    async testPerformanceFeatures() {
        console.log('Testing performance features...');

        const performanceTests = [
            { name: 'Performance API', test: () => typeof performance !== 'undefined' },
            { name: 'Performance Timing', test: () => performance.timing !== undefined },
            { name: 'Performance Navigation', test: () => performance.navigation !== undefined },
            { name: 'Performance Memory', test: () => performance.memory !== undefined },
            { name: 'Performance Observer', test: () => typeof PerformanceObserver !== 'undefined' },
            { name: 'Request Animation Frame', test: () => typeof requestAnimationFrame !== 'undefined' },
            { name: 'Intersection Observer', test: () => typeof IntersectionObserver !== 'undefined' },
            { name: 'Mutation Observer', test: () => typeof MutationObserver !== 'undefined' },
            { name: 'Web Workers', test: () => typeof Worker !== 'undefined' },
            { name: 'Service Workers', test: () => 'serviceWorker' in navigator }
        ];

        for (const test of performanceTests) {
            try {
                const result = test.test();
                this.results.performance.push({
                    name: test.name,
                    status: result ? 'pass' : 'warn',
                    message: result ? 'Supported' : 'Not available'
                });
            } catch (error) {
                this.results.performance.push({
                    name: test.name,
                    status: 'fail',
                    message: `Error: ${error.message}`
                });
            }
        }

        // Test actual performance metrics
        if (performance.timing) {
            const timing = performance.timing;
            const loadTime = timing.loadEventEnd - timing.navigationStart;
            const domReady = timing.domContentLoadedEventEnd - timing.navigationStart;

            this.results.performance.push({
                name: 'Page Load Time',
                status: loadTime < 3000 ? 'pass' : 'warn',
                message: `${loadTime}ms (${loadTime < 3000 ? 'Good' : 'Could be improved'})`
            });

            this.results.performance.push({
                name: 'DOM Ready Time',
                status: domReady < 1500 ? 'pass' : 'warn',
                message: `${domReady}ms (${domReady < 1500 ? 'Good' : 'Could be improved'})`
            });
        }
    }

    displayResults() {
        this.displayResultSection('core-features-results', this.results.core, 'Core JavaScript Features');
        this.displayResultSection('css-features-results', this.results.css, 'CSS Features');
        this.displayResultSection('responsive-results', this.results.responsive, 'Responsive Design');
        this.displayResultSection('accessibility-results', this.results.accessibility, 'Accessibility');
        this.displayResultSection('performance-results', this.results.performance, 'Performance');

        this.generateCompatibilityReport();
    }

    displayResultSection(containerId, results, sectionName) {
        const container = document.getElementById(containerId);
        if (!container) return;

        const passCount = results.filter(r => r.status === 'pass').length;
        const failCount = results.filter(r => r.status === 'fail').length;
        const warnCount = results.filter(r => r.status === 'warn').length;

        let html = `
            <div class="feature-grid">
                <div class="feature-card">
                    <h4>Summary</h4>
                    <div>✅ Passed: ${passCount}</div>
                    <div>⚠️ Warnings: ${warnCount}</div>
                    <div>❌ Failed: ${failCount}</div>
                    <div><strong>Total: ${results.length}</strong></div>
                </div>
            </div>
            <div class="test-results">
        `;

        results.forEach(result => {
            const statusClass = `test-${result.status}`;
            const statusIcon = result.status === 'pass' ? '✅' : result.status === 'warn' ? '⚠️' : '❌';
            html += `
                <div class="test-result ${statusClass}">
                    ${statusIcon} <strong>${result.name}:</strong> ${result.message}
                </div>
            `;
        });

        html += '</div>';
        container.innerHTML = html;
    }

    generateCompatibilityReport() {
        const allResults = [
            ...this.results.core,
            ...this.results.css,
            ...this.results.responsive,
            ...this.results.accessibility,
            ...this.results.performance
        ];

        const totalTests = allResults.length;
        const passedTests = allResults.filter(r => r.status === 'pass').length;
        const warningTests = allResults.filter(r => r.status === 'warn').length;
        const failedTests = allResults.filter(r => r.status === 'fail').length;

        const compatibilityScore = Math.round((passedTests + warningTests * 0.5) / totalTests * 100);

        console.log(`
🌐 BROWSER COMPATIBILITY REPORT
================================
Total Tests: ${totalTests}
Passed: ${passedTests} (${Math.round(passedTests/totalTests*100)}%)
Warnings: ${warningTests} (${Math.round(warningTests/totalTests*100)}%)
Failed: ${failedTests} (${Math.round(failedTests/totalTests*100)}%)

Overall Compatibility Score: ${compatibilityScore}%

Browser: ${navigator.userAgent}
        `);

        // Add summary to page
        const summaryDiv = document.createElement('div');
        summaryDiv.className = 'test-section';
        summaryDiv.innerHTML = `
            <h2>📊 Overall Compatibility Report</h2>
            <div class="feature-grid">
                <div class="feature-card">
                    <h3>Compatibility Score: ${compatibilityScore}%</h3>
                    <div>Total Tests: ${totalTests}</div>
                    <div class="test-pass">✅ Passed: ${passedTests}</div>
                    <div class="test-warn">⚠️ Warnings: ${warningTests}</div>
                    <div class="test-fail">❌ Failed: ${failedTests}</div>
                </div>
                <div class="feature-card">
                    <h3>Recommendations</h3>
                    ${this.generateRecommendations(compatibilityScore, failedTests)}
                </div>
            </div>
        `;
        document.querySelector('.test-container').appendChild(summaryDiv);
    }

    generateRecommendations(score, failedCount) {
        if (score >= 90) {
            return '<div class="test-pass">✅ Excellent compatibility! All core features supported.</div>';
        } else if (score >= 75) {
            return '<div class="test-warn">⚠️ Good compatibility with minor limitations. Consider polyfills for missing features.</div>';
        } else if (score >= 60) {
            return '<div class="test-warn">⚠️ Moderate compatibility. Some features may not work as expected. Update browser if possible.</div>';
        } else {
            return '<div class="test-fail">❌ Limited compatibility. Many features may not work. Browser update strongly recommended.</div>';
        }
    }
}

// Auto-run tests when page loads
document.addEventListener('DOMContentLoaded', async () => {
    const tester = new BrowserCompatibilityTester();
    await tester.runAllTests();
});

// Export for manual testing
window.BrowserCompatibilityTester = BrowserCompatibilityTester;