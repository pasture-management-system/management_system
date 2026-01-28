/**
 * 清發畜牧場管理系統 - 主要 JavaScript
 */

// ============== 工具函數 ==============

/**
 * 格式化貨幣
 */
function formatCurrency(amount) {
    if (amount === null || amount === undefined) return '-';
    return new Intl.NumberFormat('zh-TW', {
        style: 'currency',
        currency: 'TWD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(amount);
}

/**
 * 格式化數字
 */
function formatNumber(num, decimals = 2) {
    if (num === null || num === undefined) return '-';
    return new Intl.NumberFormat('zh-TW', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    }).format(num);
}

/**
 * 格式化日期
 */
function formatDate(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleDateString('zh-TW');
}

/**
 * 西元年轉民國年
 */
function toROCDate(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    const rocYear = date.getFullYear() - 1911;
    return `${rocYear}/${String(date.getMonth() + 1).padStart(2, '0')}/${String(date.getDate()).padStart(2, '0')}`;
}

/**
 * 取得今天日期 (YYYY-MM-DD)
 */
function getToday() {
    return new Date().toISOString().split('T')[0];
}

// ============== Toast 通知 ==============

function showToast(message, type = 'success') {
    const toastContainer = document.getElementById('toast-container') || createToastContainer();
    
    const toastId = 'toast-' + Date.now();
    const bgClass = {
        'success': 'bg-success',
        'error': 'bg-danger',
        'warning': 'bg-warning',
        'info': 'bg-info'
    }[type] || 'bg-success';
    
    const toastHtml = `
        <div id="${toastId}" class="toast align-items-center text-white ${bgClass} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">
                    <i class="bi bi-${type === 'success' ? 'check-circle' : type === 'error' ? 'x-circle' : 'info-circle'} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, { delay: 3000 });
    toast.show();
    
    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '9999';
    document.body.appendChild(container);
    return container;
}

// ============== 確認對話框 ==============

function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// ============== 表單處理 ==============

/**
 * 序列化表單數據
 */
function serializeForm(formElement) {
    const formData = new FormData(formElement);
    const data = {};
    formData.forEach((value, key) => {
        if (data[key]) {
            if (!Array.isArray(data[key])) {
                data[key] = [data[key]];
            }
            data[key].push(value);
        } else {
            data[key] = value;
        }
    });
    return data;
}

/**
 * 提交表單 (AJAX)
 */
async function submitForm(formElement, successCallback) {
    const formData = new FormData(formElement);
    const url = formElement.action;
    const method = formElement.method || 'POST';
    
    try {
        const response = await fetch(url, {
            method: method.toUpperCase(),
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast(result.message || '操作成功', 'success');
            if (successCallback) {
                successCallback(result);
            }
        } else {
            showToast(result.detail || result.message || '操作失敗', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('系統錯誤，請稍後再試', 'error');
    }
}

// ============== API 呼叫 ==============

/**
 * API GET 請求
 */
async function apiGet(url) {
    try {
        const response = await fetch(url);
        return await response.json();
    } catch (error) {
        console.error('API GET Error:', error);
        showToast('載入資料失敗', 'error');
        return { success: false, error: error.message };
    }
}

/**
 * API POST 請求
 */
async function apiPost(url, data) {
    try {
        const formData = new FormData();
        Object.keys(data).forEach(key => {
            if (data[key] !== null && data[key] !== undefined) {
                formData.append(key, data[key]);
            }
        });
        
        const response = await fetch(url, {
            method: 'POST',
            body: formData
        });
        
        return await response.json();
    } catch (error) {
        console.error('API POST Error:', error);
        showToast('操作失敗', 'error');
        return { success: false, error: error.message };
    }
}

// ============== 表格功能 ==============

/**
 * 初始化可排序表格
 */
function initSortableTable(tableId) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const headers = table.querySelectorAll('th[data-sort]');
    headers.forEach(header => {
        header.style.cursor = 'pointer';
        header.addEventListener('click', () => {
            const sortKey = header.dataset.sort;
            const currentOrder = header.dataset.order || 'asc';
            const newOrder = currentOrder === 'asc' ? 'desc' : 'asc';
            
            // 更新排序圖示
            headers.forEach(h => {
                h.dataset.order = '';
                h.querySelector('.sort-icon')?.remove();
            });
            
            header.dataset.order = newOrder;
            header.insertAdjacentHTML('beforeend', `
                <i class="bi bi-arrow-${newOrder === 'asc' ? 'up' : 'down'} sort-icon ms-1"></i>
            `);
            
            // 排序表格
            sortTable(table, sortKey, newOrder);
        });
    });
}

/**
 * 排序表格
 */
function sortTable(table, sortKey, order) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    rows.sort((a, b) => {
        const aVal = a.querySelector(`td[data-sort-value="${sortKey}"]`)?.dataset.value || 
                     a.querySelector(`td:nth-child(${getColumnIndex(table, sortKey)})`)?.textContent || '';
        const bVal = b.querySelector(`td[data-sort-value="${sortKey}"]`)?.dataset.value || 
                     b.querySelector(`td:nth-child(${getColumnIndex(table, sortKey)})`)?.textContent || '';
        
        // 數字比較
        if (!isNaN(aVal) && !isNaN(bVal)) {
            return order === 'asc' ? aVal - bVal : bVal - aVal;
        }
        
        // 字串比較
        return order === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
    });
    
    rows.forEach(row => tbody.appendChild(row));
}

function getColumnIndex(table, sortKey) {
    const headers = table.querySelectorAll('th');
    for (let i = 0; i < headers.length; i++) {
        if (headers[i].dataset.sort === sortKey) {
            return i + 1;
        }
    }
    return 1;
}

// ============== 搜尋功能 ==============

/**
 * 初始化表格搜尋
 */
function initTableSearch(inputId, tableId) {
    const input = document.getElementById(inputId);
    const table = document.getElementById(tableId);
    
    if (!input || !table) return;
    
    input.addEventListener('input', function() {
        const searchText = this.value.toLowerCase();
        const rows = table.querySelectorAll('tbody tr');
        
        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(searchText) ? '' : 'none';
        });
    });
}

// ============== 分頁功能 ==============

function renderPagination(containerId, currentPage, totalPages, callback) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    let html = '<nav><ul class="pagination mb-0">';
    
    // 上一頁
    html += `
        <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" data-page="${currentPage - 1}">
                <i class="bi bi-chevron-left"></i>
            </a>
        </li>
    `;
    
    // 頁碼
    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);
    
    if (startPage > 1) {
        html += `<li class="page-item"><a class="page-link" href="#" data-page="1">1</a></li>`;
        if (startPage > 2) {
            html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
    }
    
    for (let i = startPage; i <= endPage; i++) {
        html += `
            <li class="page-item ${i === currentPage ? 'active' : ''}">
                <a class="page-link" href="#" data-page="${i}">${i}</a>
            </li>
        `;
    }
    
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
        html += `<li class="page-item"><a class="page-link" href="#" data-page="${totalPages}">${totalPages}</a></li>`;
    }
    
    // 下一頁
    html += `
        <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
            <a class="page-link" href="#" data-page="${currentPage + 1}">
                <i class="bi bi-chevron-right"></i>
            </a>
        </li>
    `;
    
    html += '</ul></nav>';
    container.innerHTML = html;
    
    // 綁定事件
    container.querySelectorAll('.page-link[data-page]').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const page = parseInt(this.dataset.page);
            if (page >= 1 && page <= totalPages && page !== currentPage) {
                callback(page);
            }
        });
    });
}

// ============== 列印功能 ==============

function printContent(elementId) {
    const content = document.getElementById(elementId);
    if (!content) return;
    
    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
        <!DOCTYPE html>
        <html>
        <head>
            <title>列印</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                body { padding: 20px; }
                @media print {
                    .no-print { display: none !important; }
                }
            </style>
        </head>
        <body>
            ${content.innerHTML}
            <script>
                window.onload = function() {
                    window.print();
                    window.close();
                };
            </script>
        </body>
        </html>
    `);
    printWindow.document.close();
}

// ============== 初始化 ==============

document.addEventListener('DOMContentLoaded', function() {
    // 自動設置今天日期
    document.querySelectorAll('input[type="date"][data-default-today]').forEach(input => {
        if (!input.value) {
            input.value = getToday();
        }
    });
    
    // 初始化 tooltips
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltipTriggerList.forEach(el => new bootstrap.Tooltip(el));
    
    // 表單驗證樣式
    document.querySelectorAll('.needs-validation').forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
});
