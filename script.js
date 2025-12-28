const today = new Date();
const formatDate = (date) => {
    return `${date.getFullYear()}年${date.getMonth() + 1}月${date.getDate()}日`;
};

// カテゴリ設定
const POOL_ITEMS = [];
const POOL_AGENCIES = ["農林水産省", "林野庁", "水産庁", "農水省"];
const MOCK_DATA = [];

function getCategoryLabel(cat) {
    const map = {
        'agriculture': '農業',
        'food': '食品',
        'other': 'その他'
    };
    return map[cat] || 'その他';
}

document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Elements ---
    const listContainer = document.getElementById('bid-list');
    const tabs = document.querySelectorAll('.tab');
    const statusDot = document.querySelector('.status-dot');
    const updateBtn = document.getElementById('update-btn');

    // Initial Overlay Elements
    const overlay = document.getElementById('initial-overlay');
    const startBtn = document.getElementById('start-btn');
    const loadingContainer = document.getElementById('loading-container');

    // --- State ---
    let currentItems = [];

    // Load initial data if available (e.g. from server pre-fetch)
    if (window.GENERATED_BID_DATA && window.GENERATED_BID_DATA.length > 0) {
        currentItems = [...window.GENERATED_BID_DATA];
    } else {
        currentItems = [...MOCK_DATA];
    }

    // --- Functions ---

    // Render the list of items
    function renderList(items) {
        listContainer.innerHTML = '';
        if (items.length === 0) {
            listContainer.innerHTML = '<div style="text-align:center; padding: 2rem; color: #666;">該当する案件はありません</div>';
            return;
        }

        // Sort by date descending
        const sortedItems = [...items].sort((a, b) => new Date(b.date) - new Date(a.date));

        sortedItems.forEach(item => {
            const div = document.createElement('div');
            div.className = 'bid-item';
            div.dataset.category = item.category;

            const searchUrl = item.url ? item.url : `https://www.kkj.go.jp/s/?X=検索&ti=${encodeURIComponent(item.title)}`;

            div.innerHTML = `
                <div class="bid-header">
                    <span class="bid-category cat-${item.category}">${getCategoryLabel(item.category)}</span>
                    <span class="bid-date">${item.date}</span>
                </div>
                <a href="${searchUrl}" target="_blank" class="bid-title" rel="noopener noreferrer">
                    ${item.title}
                    <span class="external-link-icon">↗</span>
                </a>
                <div class="bid-agency">発注機関: ${item.agency}</div>
            `;
            listContainer.appendChild(div);
        });
    }

    // Filter by category
    function filterAndRender(category) {
        if (category === 'all') {
            renderList(currentItems);
        } else {
            const filtered = currentItems.filter(item => item.category === category);
            renderList(filtered);
        }
    }

    // Fetch data from server API
    async function fetchLatestData(isInitial = false) {
        // UI updates for Initial vs Update
        if (isInitial) {
            if (startBtn) startBtn.style.display = 'none';
            if (loadingContainer) loadingContainer.style.display = 'flex';
        } else {
            if (updateBtn) {
                if (updateBtn.classList.contains('loading')) return;
                updateBtn.classList.add('loading');
                updateBtn.textContent = '更新中...';
                if (statusDot) statusDot.classList.add('loading');
            }
        }

        try {
            console.log("Fetching latest data from server...");
            const response = await fetch('/api/update');
            if (!response.ok) {
                console.log("Server API not available.");
                return;
            }

            const data = await response.json();
            console.log("Data fetched:", data);

            if (data && data.length > 0) {
                currentItems = data;
                // Re-render
                const activeTab = document.querySelector('.tab.active');
                const activeCategory = activeTab ? activeTab.dataset.category : 'all';
                filterAndRender(activeCategory);
                console.log("Updated with latest server data.");
            } else if (isInitial) {
                // Even if empty, we might want to refresh to show empty state
                currentItems = [];
                filterAndRender('all');
            }

        } catch (e) {
            console.error("Fetch failed:", e);
        } finally {
            // Clean up UI
            if (isInitial) {
                // Wait a bit then hide overlay
                setTimeout(() => {
                    if (overlay) overlay.classList.add('hidden');
                }, 800);
            } else {
                if (updateBtn) {
                    updateBtn.classList.remove('loading');
                    updateBtn.textContent = '情報更新';
                }
                if (statusDot) statusDot.classList.remove('loading');
            }
        }
    }

    // --- Event Listeners ---

    // Tabs
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            filterAndRender(tab.dataset.category);
        });
    });

    // Update Button (Top Right)
    if (updateBtn) {
        updateBtn.addEventListener('click', () => fetchLatestData(false));
    }

    // Start Button (Overlay)
    if (startBtn) {
        console.log("Start button found, attaching listener.");
        startBtn.addEventListener('click', () => {
            console.log("Start button clicked.");
            fetchLatestData(true);
        });
    } else {
        console.error("Start button not found!");
    }

    // --- Initialization ---
    // Initial Render (likely empty or pre-fetched data)
    renderList(currentItems);

});
