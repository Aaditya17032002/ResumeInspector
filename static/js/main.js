// Initialize PDF.js
pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

// Configuration
const BACKEND_URL = 'http://localhost:8000';  // FastAPI backend URL

// DOM Elements
const sidebar = document.getElementById('sidebar');
const mainContent = document.getElementById('mainContent');
const toggleSidebarBtn = document.getElementById('toggleSidebar');
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const fileInfo = document.getElementById('fileInfo');
const fileName = document.getElementById('fileName');
const previewContainer = document.getElementById('previewContainer');
const pdfPreview = document.getElementById('pdfPreview');
const textPreview = document.getElementById('textPreview');
const noPreview = document.getElementById('noPreview');
const analysisSection = document.getElementById('analysisSection');
const analyzeBtn = document.getElementById('analyzeBtn');
const loadingState = document.getElementById('loadingState');
const results = document.getElementById('results');
const modal = document.getElementById('contentModal');
const modalTitle = document.getElementById('modalTitle');
const modalContent = document.getElementById('modalContent');

// Allowed file types
const ALLOWED_FILE_TYPES = [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/octet-stream'  // Some .doc files might be detected as this
];

const ALLOWED_EXTENSIONS = ['.pdf', '.doc', '.docx'];

// Current file state
let currentFile = null;

// Sidebar toggle
toggleSidebarBtn.addEventListener('click', () => {
    sidebar.classList.toggle('collapsed');
    mainContent.classList.toggle('expanded');
    document.querySelectorAll('.sidebar-text').forEach(el => {
        el.classList.toggle('hidden');
    });
});

// Tab handling
document.querySelectorAll('.tab-button').forEach(button => {
    button.addEventListener('click', () => {
        // Remove active class from all buttons and panes
        document.querySelectorAll('.tab-button').forEach(btn => {
            btn.classList.remove('active', 'text-blue-600', 'border-blue-600');
            btn.classList.add('text-gray-500');
        });
        document.querySelectorAll('.tab-pane').forEach(pane => {
            pane.classList.add('hidden');
        });

        // Add active class to clicked button and corresponding pane
        button.classList.add('active', 'text-blue-600', 'border-blue-600');
        button.classList.remove('text-gray-500');
        const tabId = button.getAttribute('data-tab');
        document.getElementById(tabId).classList.remove('hidden');
    });
});

// Modal handling
function openModal(title, content) {
    modalTitle.textContent = title;
    modalContent.innerHTML = content;
    modal.style.display = 'block';
    document.body.style.overflow = 'hidden';
}

function closeModal() {
    modal.style.display = 'none';
    document.body.style.overflow = 'auto';
}

// Close modal when clicking outside
modal.addEventListener('click', (e) => {
    if (e.target === modal) {
        closeModal();
    }
});

// Drag and drop handlers
dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropZone.classList.add('border-blue-500', 'bg-blue-50');
});

dropZone.addEventListener('dragleave', (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropZone.classList.remove('border-blue-500', 'bg-blue-50');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropZone.classList.remove('border-blue-500', 'bg-blue-50');
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFile(e.target.files[0]);
    }
});

// Add click handler for Browse Files button to trigger file input
const browseBtn = document.querySelector('#dropZone button.btn-primary');
if (browseBtn) {
    browseBtn.addEventListener('click', (e) => {
        e.preventDefault();
        fileInput.click();
    });
}

// File handling
function handleFile(file) {
    // Check file extension
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(fileExtension)) {
        showError('Please upload a PDF or Word document (.pdf, .doc, or .docx)');
        return;
    }

    // For .doc files that might be detected as application/octet-stream
    if (fileExtension === '.doc' && file.type === 'application/octet-stream') {
        // Allow this case
    } else if (!ALLOWED_FILE_TYPES.includes(file.type)) {
        showError('Invalid file type. Please upload a PDF or Word document.');
        return;
    }

    currentFile = file;
    fileName.textContent = file.name;
    fileInfo.classList.remove('hidden');
    analysisSection.classList.remove('hidden');
    analyzeBtn.classList.remove('hidden');
    
    // Show preview
    if (file.type === 'application/pdf') {
        showPdfPreview(file);
    } else {
        showTextPreview(file);
    }

    // Automatically switch to Analysis tab and start analysis
    sections.forEach(sec => sec.classList.add('hidden'));
    document.getElementById('analysisTab').classList.remove('hidden');
    sidebarTabs.forEach(t => t.classList.remove('bg-gray-700', 'text-white'));
    sidebarTabs[2].classList.add('bg-gray-700', 'text-white');
    // Start analysis automatically
    analyzeBtn.click();
}

function showError(message) {
    // Create error toast
    const toast = document.createElement('div');
    toast.className = 'fixed top-4 right-4 bg-red-500 text-white px-6 py-3 rounded-lg shadow-lg transform transition-transform duration-300 translate-y-[-100%] z-50';
    toast.textContent = message;
    document.body.appendChild(toast);

    // Animate in
    setTimeout(() => {
        toast.style.transform = 'translateY(0)';
    }, 100);

    // Remove after 3 seconds
    setTimeout(() => {
        toast.style.transform = 'translateY(-100%)';
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 300);
    }, 3000);
}

function removeFile() {
    currentFile = null;
    fileInput.value = '';
    fileInfo.classList.add('hidden');
    analysisSection.classList.add('hidden');
    analyzeBtn.classList.add('hidden');
    results.classList.add('hidden');
    previewContainer.innerHTML = `
        <div id="noPreview" class="flex flex-col items-center justify-center h-96 text-gray-500">
            <div class="w-24 h-24 bg-gray-100 rounded-2xl flex items-center justify-center mb-6">
                <i class="fas fa-file-alt text-4xl text-gray-400"></i>
            </div>
            <h4 class="text-xl font-medium mb-2">No Document Uploaded</h4>
            <p>Upload a resume to see the preview here</p>
        </div>
        <div id="pdfPreview" class="hidden p-4"></div>
        <div id="textPreview" class="hidden p-6"></div>
    `;
}

// Preview handlers
async function showPdfPreview(file) {
    pdfPreview.classList.remove('hidden');
    textPreview.classList.add('hidden');
    noPreview.classList.add('hidden');

    const arrayBuffer = await file.arrayBuffer();
    const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
    
    // Render first page
    const page = await pdf.getPage(1);
    const viewport = page.getViewport({ scale: 1.5 });
    
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    canvas.height = viewport.height;
    canvas.width = viewport.width;
    
    pdfPreview.innerHTML = '';
    pdfPreview.appendChild(canvas);
    
    await page.render({
        canvasContext: context,
        viewport: viewport
    }).promise;

    // Add click handler to open in modal
    canvas.addEventListener('click', () => {
        openModal('Resume Preview', `
            <div class="flex justify-center">
                <img src="${canvas.toDataURL()}" alt="Resume Preview" class="max-w-full">
            </div>
        `);
    });
}

async function showTextPreview(file) {
    pdfPreview.classList.add('hidden');
    textPreview.classList.remove('hidden');
    noPreview.classList.add('hidden');
    textPreview.innerHTML = '';

    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();

    if (fileExtension === '.docx') {
        // Use mammoth.js to extract text from docx
        const arrayBuffer = await file.arrayBuffer();
        mammoth.convertToHtml({ arrayBuffer: arrayBuffer })
            .then(function(resultObject) {
                const html = resultObject.value;
                const div = document.createElement('div');
                div.innerHTML = html;
                div.className = 'prose max-w-none cursor-pointer';
                textPreview.appendChild(div);

                // Add click handler to open in modal
                div.addEventListener('click', () => {
                    openModal('Resume Text', `<div class="bg-gray-50 p-4 rounded-lg">${html}</div>`);
                });
            })
            .catch(function(err) {
                textPreview.innerHTML = '<div class="text-red-500">Failed to preview DOCX file.</div>';
            });
    } else if (fileExtension === '.doc') {
        textPreview.innerHTML = '<div class="text-yellow-600">Preview not supported for .doc files. Please use PDF or DOCX for preview.</div>';
    } else {
        // Try to read as plain text
        const text = await file.text();
        const pre = document.createElement('pre');
        pre.className = 'whitespace-pre-wrap cursor-pointer';
        pre.textContent = text;
        textPreview.appendChild(pre);

        // Add click handler to open in modal
        pre.addEventListener('click', () => {
            openModal('Resume Text', `<div class="bg-gray-50 p-4 rounded-lg"><pre class="whitespace-pre-wrap">${text}</pre></div>`);
        });
    }
}

// Analysis handlers
analyzeBtn.addEventListener('click', async () => {
    if (!currentFile) return;
    
    loadingState.classList.remove('hidden');
    results.classList.add('hidden');
    analyzeBtn.disabled = true;
    
    const formData = new FormData();
    formData.append('file', currentFile);
    
    try {
        const response = await fetch(`${BACKEND_URL}/analyze`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || 'Analysis failed');
        }
        
        const data = await response.json();
        console.log('Received analysis data:', data);
        displayResults(data);
    } catch (error) {
        console.error('Analysis error:', error);
        showError(error.message || 'Failed to analyze resume. Please try again.');
    } finally {
        loadingState.classList.add('hidden');
        analyzeBtn.disabled = false;
    }
});

function displayResults(data) {
    console.log('displayResults called', data);
    setGlow(data.status);
    // Show analysis tab
    sections.forEach(sec => sec.classList.add('hidden'));
    document.getElementById('analysisTab').classList.remove('hidden');
    sidebarTabs.forEach(t => t.classList.remove('bg-gray-700', 'text-white'));
    sidebarTabs[2].classList.add('bg-gray-700', 'text-white');

    // Modern Summary Card
    const summary = document.getElementById('modernSummary');
    const verdictIcon = document.getElementById('modernVerdictIcon');
    const verdictText = document.getElementById('modernVerdictText');
    const confidence = document.getElementById('modernConfidence');
    const assessment = document.getElementById('modernAssessment');
    if (summary && verdictIcon && verdictText && confidence && assessment) {
        summary.style.display = '';
        if (data.status === 'LEGIT') {
            summary.className = 'rounded-xl shadow-lg p-6 flex items-center gap-6 mb-4 border-2 border-green-400 bg-green-50';
            verdictIcon.innerHTML = '<i class="fas fa-check-circle text-green-500"></i>';
            verdictText.textContent = 'LEGIT';
            confidence.textContent = `${data.confidence_score}% Confidence`;
            confidence.className = 'text-lg font-semibold text-green-700';
        } else {
            summary.className = 'rounded-xl shadow-lg p-6 flex items-center gap-6 mb-4 border-2 border-red-400 bg-red-50';
            verdictIcon.innerHTML = '<i class="fas fa-times-circle text-red-500"></i>';
            verdictText.textContent = 'FAKE';
            confidence.textContent = `${data.confidence_score}% Confidence`;
            confidence.className = 'text-lg font-semibold text-red-700';
        }
        // Show overall assessment if available
        if (data.overall_assessment) {
            assessment.textContent = data.overall_assessment;
        } else if (data.analysis && data.analysis.overall_assessment) {
            assessment.textContent = data.analysis.overall_assessment;
        } else {
            assessment.textContent = '';
        }
    }

    // Helper to render items as unique cards
    function renderUniqueCards(items, type) {
        if (!items || !items.length) return '<div class="text-gray-400">None</div>';
        // Icon and color by type
        let icon, color, badge;
        switch(type) {
            case 'key':
                icon = '<i class="fas fa-search text-blue-500"></i>';
                color = 'blue';
                badge = 'Key';
                break;
            case 'suspicious':
                icon = '<i class="fas fa-exclamation-triangle text-yellow-500"></i>';
                color = 'yellow';
                badge = 'Suspicious';
                break;
            case 'missing':
                icon = '<i class="fas fa-info-circle text-gray-500"></i>';
                color = 'gray';
                badge = 'Missing';
                break;
            case 'improve':
                icon = '<i class="fas fa-lightbulb text-green-500"></i>';
                color = 'green';
                badge = 'Tip';
                break;
            default:
                icon = '<i class="fas fa-file-alt text-blue-400"></i>';
                color = 'blue';
                badge = '';
        }
        return items.map((item, idx) => {
            // Try to use title/description/details, fallback to string
            let title = item.title || item.heading || badge + ' #' + (idx+1);
            let desc = item.description || item.details || (typeof item === 'string' ? item : '');
            return `
                <div class="rounded-xl p-5 mb-3 bg-${color}-50 border-l-8 border-${color}-400 shadow flex items-start gap-4 hover:scale-[1.02] transition-transform">
                    <div class="text-2xl mt-1">${icon}</div>
                    <div class="flex-1">
                        <div class="flex items-center gap-2 mb-1">
                            <span class="inline-block px-2 py-0.5 text-xs rounded-full bg-${color}-200 text-${color}-800 font-semibold">${badge}</span>
                            <span class="font-bold text-${color}-800 text-lg">${title}</span>
                        </div>
                        <div class="text-${color}-700 text-base">${desc}</div>
                    </div>
                </div>
            `;
        }).join('');
    }

    // Populate panels and badges
    // Key Findings
    const keyFindings = data.key_findings || (data.analysis && data.analysis.key_findings) || [];
    document.getElementById('panelKeyFindingsBody').innerHTML = renderUniqueCards(keyFindings, 'key');
    document.getElementById('badgeKeyFindings').textContent = keyFindings.length;
    // Suspicious Elements
    const suspicious = data.suspicious_elements || (data.analysis && data.analysis.suspicious_elements) || [];
    document.getElementById('panelSuspiciousBody').innerHTML = renderUniqueCards(suspicious, 'suspicious');
    document.getElementById('badgeSuspicious').textContent = suspicious.length;
    // Missing Info
    const missing = data.missing_information || data.missing_elements || (data.analysis && (data.analysis.missing_information || data.analysis.missing_elements)) || [];
    document.getElementById('panelMissingBody').innerHTML = renderUniqueCards(missing, 'missing');
    document.getElementById('badgeMissing').textContent = missing.length;
    // Recommendations
    const improvements = data.improvements || data.recommendations || [];
    document.getElementById('panelImprovementsBody').innerHTML = renderUniqueCards(improvements, 'improve');
    document.getElementById('badgeImprovements').textContent = improvements.length;

    // Show results
    results.classList.remove('hidden');
}

// Utility functions
function formatDate(date) {
    return new Date(date).toLocaleDateString();
}

// Error handling
window.addEventListener('error', (e) => {
    console.error('Global error:', e.error);
    showError('An error occurred. Please try again.');
});

// Sidebar tab switching
const sidebarTabs = document.querySelectorAll('.sidebar-tab');
const sections = [
    document.getElementById('uploadTab'),
    document.getElementById('previewTab'),
    document.getElementById('analysisTab')
];
sidebarTabs.forEach((tab, idx) => {
    tab.addEventListener('click', (e) => {
        e.preventDefault();
        sidebarTabs.forEach(t => t.classList.remove('bg-gray-700', 'text-white'));
        tab.classList.add('bg-gray-700', 'text-white');
        sections.forEach(sec => sec.classList.add('hidden'));
        sections[idx].classList.remove('hidden');
    });
});
// Default to Upload tab
sections.forEach(sec => sec.classList.add('hidden'));
document.getElementById('uploadTab').classList.remove('hidden');
sidebarTabs[0].classList.add('bg-gray-700', 'text-white');

// Border glow on verdict
function setGlow(status) {
    document.body.classList.remove('glow-legit', 'glow-fake');
    if (status === 'LEGIT') {
        document.body.classList.add('glow-legit');
    } else if (status === 'FAKE') {
        document.body.classList.add('glow-fake');
    }
}
function clearGlow() {
    document.body.classList.remove('glow-legit', 'glow-fake');
} 