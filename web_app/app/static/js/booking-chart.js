/**
 * Booking Chart Component
 * Renders interactive booking charts for defragmentation moves display
 */

class BookingChart {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = {
            showTooltips: true,
            allowToggle: true,
            responsiveBreakpoint: 768,
            ...options
        };
        this.chartData = null;
        this.tooltip = null;
        this.init();
    }

    init() {
        if (!this.container) {
            console.error('BookingChart: Container not found');
            return;
        }
        
        this.createTooltip();
        this.bindEvents();
    }

    createTooltip() {
        if (!this.options.showTooltips) return;
        
        this.tooltip = document.createElement('div');
        this.tooltip.className = 'booking-tooltip';
        this.tooltip.style.display = 'none';
        document.body.appendChild(this.tooltip);
    }

    bindEvents() {
        // Responsive handling
        window.addEventListener('resize', this.handleResize.bind(this));
    }

    async loadChart(propertyCode) {
        try {
            this.showLoading();
            
            const response = await fetch(`/api/v1/chart/booking-chart/${propertyCode}`, {
                headers: {
                    'Authorization': `Bearer ${authToken || localStorage.getItem('authToken')}`
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            
            if (result.success && result.data) {
                this.chartData = result.data;
                this.renderChart();
            } else {
                this.showError('No chart data available. Please run defragmentation analysis first.');
            }
        } catch (error) {
            console.error('Error loading chart:', error);
            this.showError('Failed to load booking chart data.');
        }
    }

    renderChart() {
        if (!this.chartData || !this.chartData.categories) {
            this.showNoData();
            return;
        }

        this.container.innerHTML = '';
        
        const chartContainer = document.createElement('div');
        chartContainer.className = 'booking-chart-container';

        // Render each category
        this.chartData.categories.forEach((category, index) => {
            const categoryElement = this.renderCategory(category, index);
            chartContainer.appendChild(categoryElement);
        });

        this.container.appendChild(chartContainer);
    }

    renderCategory(category, index) {
        const categoryDiv = document.createElement('div');
        categoryDiv.className = 'chart-category';
        categoryDiv.setAttribute('data-category', index);

        // Category header
        const header = document.createElement('div');
        header.className = 'category-header';
        header.innerHTML = `
            <span>${category.name}</span>
            <button class="category-toggle" data-target="chart-${index}">
                ▶
            </button>
        `;

        // Chart grid (initially hidden)
        const gridDiv = document.createElement('div');
        gridDiv.className = 'chart-grid';
        gridDiv.id = `chart-${index}`;

        if (category.units && category.units.length > 0) {
            const table = this.createChartTable(category);
            gridDiv.appendChild(table);
        } else {
            gridDiv.innerHTML = '<div class="chart-no-data">No units found for this category</div>';
        }

        // Toggle functionality
        header.addEventListener('click', () => {
            this.toggleCategory(index);
        });

        categoryDiv.appendChild(header);
        categoryDiv.appendChild(gridDiv);

        return categoryDiv;
    }

    createChartTable(category) {
        const table = document.createElement('table');
        table.className = 'booking-chart-table';

        // Create header row
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        headerRow.className = 'chart-header-row';

        // Unit header
        const unitHeader = document.createElement('th');
        unitHeader.className = 'chart-header-cell';
        unitHeader.textContent = 'Unit/Site';
        headerRow.appendChild(unitHeader);

        // Date headers
        this.chartData.date_range.forEach(dateStr => {
            const dateHeader = document.createElement('th');
            dateHeader.className = 'chart-header-cell';
            
            // Format date for display (DD/MM)
            const date = new Date(dateStr + 'T00:00:00');
            dateHeader.textContent = date.toLocaleDateString('en-AU', {
                day: '2-digit',
                month: '2-digit'
            });
            
            headerRow.appendChild(dateHeader);
        });

        thead.appendChild(headerRow);
        table.appendChild(thead);

        // Create body
        const tbody = document.createElement('tbody');
        
        category.units.forEach(unit => {
            const row = this.createUnitRow(unit);
            tbody.appendChild(row);
        });

        table.appendChild(tbody);
        return table;
    }

    createUnitRow(unit) {
        const row = document.createElement('tr');

        // Unit name cell
        const unitCell = document.createElement('td');
        unitCell.className = 'chart-unit-cell';
        unitCell.textContent = unit.unit_code;
        unitCell.title = unit.unit_code;
        row.appendChild(unitCell);

        // Create booking lookup for this unit
        const bookingLookup = this.createBookingLookup(unit.bookings);

        // Create cells for each date
        this.chartData.date_range.forEach(dateStr => {
            const cell = document.createElement('td');
            cell.className = 'chart-booking-cell';
            
            const booking = bookingLookup[dateStr];
            if (booking) {
                this.renderBookingCell(cell, booking, dateStr);
            } else {
                cell.classList.add('empty');
            }

            row.appendChild(cell);
        });

        return row;
    }

    createBookingLookup(bookings) {
        const lookup = {};
        
        bookings.forEach(booking => {
            const startDate = new Date(booking.start_date + 'T00:00:00');
            const endDate = new Date(booking.end_date + 'T00:00:00');
            
            let currentDate = new Date(startDate);
            while (currentDate <= endDate) {
                const dateStr = currentDate.toISOString().split('T')[0];
                lookup[dateStr] = booking;
                currentDate.setDate(currentDate.getDate() + 1);
            }
        });

        return lookup;
    }

    renderBookingCell(cell, booking, dateStr) {
        // Add status-based styling
        cell.classList.add(booking.color_class);
        
        // Add booking span classes
        if (booking.start_date === booking.end_date) {
            cell.classList.add('booking-span-single');
        } else {
            cell.classList.add('booking-span');
            if (booking.start_date === dateStr) {
                cell.classList.add('booking-span-start');
            }
            if (booking.end_date === dateStr) {
                cell.classList.add('booking-span-end');
            }
        }

        // Add move suggestion styling
        if (booking.is_move_suggestion) {
            cell.classList.add('move-suggestion');
        }

        // Add fixed booking styling
        if (booking.is_fixed) {
            cell.classList.add('fixed-booking');
        }

        // Set cell content
        cell.textContent = booking.guest_name;

        // Add tooltip if enabled
        if (this.options.showTooltips) {
            this.addTooltip(cell, booking);
        }
    }

    addTooltip(cell, booking) {
        cell.addEventListener('mouseenter', (e) => {
            if (!this.tooltip) return;

            const tooltipContent = this.createTooltipContent(booking);
            this.tooltip.innerHTML = tooltipContent;
            this.tooltip.style.display = 'block';
            
            this.positionTooltip(e);
        });

        cell.addEventListener('mousemove', (e) => {
            this.positionTooltip(e);
        });

        cell.addEventListener('mouseleave', () => {
            if (this.tooltip) {
                this.tooltip.style.display = 'none';
            }
        });
    }

    createTooltipContent(booking) {
        let content = `
            <div><strong>${booking.guest_name}</strong></div>
            <div>Reservation: ${booking.reservation_no}</div>
            <div>Status: ${booking.status}</div>
            <div>Check-in: ${this.formatDate(booking.start_date)}</div>
            <div>Check-out: ${this.formatDate(booking.end_date)}</div>
            <div>Nights: ${booking.nights}</div>
        `;

        if (booking.is_fixed) {
            content += `<div><strong>🎯 Fixed Booking</strong></div>`;
        }

        if (booking.is_move_suggestion) {
            content += `<div><strong>🔄 Move Suggestion</strong></div>`;
            if (booking.move_info && booking.move_info.target_unit) {
                content += `<div>Suggested Unit: ${booking.move_info.target_unit}</div>`;
            }
        }

        return content;
    }

    positionTooltip(e) {
        if (!this.tooltip) return;

        const tooltipRect = this.tooltip.getBoundingClientRect();
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;

        let left = e.clientX + 10;
        let top = e.clientY - tooltipRect.height - 10;

        // Adjust if tooltip goes off screen
        if (left + tooltipRect.width > viewportWidth) {
            left = e.clientX - tooltipRect.width - 10;
        }

        if (top < 0) {
            top = e.clientY + 10;
        }

        this.tooltip.style.left = `${left}px`;
        this.tooltip.style.top = `${top}px`;
    }

    toggleCategory(index) {
        const grid = document.getElementById(`chart-${index}`);
        const toggle = document.querySelector(`[data-target="chart-${index}"]`);
        
        if (grid && toggle) {
            if (grid.classList.contains('show')) {
                grid.classList.remove('show');
                toggle.textContent = '▶';
            } else {
                grid.classList.add('show');
                toggle.textContent = '▼';
            }
        }
    }

    expandAllCategories() {
        const grids = this.container.querySelectorAll('.chart-grid');
        const toggles = this.container.querySelectorAll('.category-toggle');
        
        grids.forEach(grid => grid.classList.add('show'));
        toggles.forEach(toggle => toggle.textContent = '▼');
    }

    collapseAllCategories() {
        const grids = this.container.querySelectorAll('.chart-grid');
        const toggles = this.container.querySelectorAll('.category-toggle');
        
        grids.forEach(grid => grid.classList.remove('show'));
        toggles.forEach(toggle => toggle.textContent = '▶');
    }

    showLoading() {
        this.container.innerHTML = `
            <div class="chart-loading">
                <div class="spinner-border" role="status">
                    <span class="visually-hidden">Loading chart...</span>
                </div>
                <div class="mt-2">Loading booking chart...</div>
            </div>
        `;
    }

    showError(message) {
        this.container.innerHTML = `
            <div class="chart-error">
                <i class="fas fa-exclamation-triangle me-2"></i>
                ${message}
            </div>
        `;
    }

    showNoData() {
        this.container.innerHTML = `
            <div class="chart-no-data">
                <i class="fas fa-calendar-times fa-2x mb-3"></i>
                <div>No booking data available</div>
            </div>
        `;
    }

    handleResize() {
        // Handle responsive adjustments if needed
        if (window.innerWidth < this.options.responsiveBreakpoint) {
            // Mobile adjustments
            this.container.classList.add('chart-mobile');
        } else {
            this.container.classList.remove('chart-mobile');
        }
    }

    formatDate(dateStr) {
        const date = new Date(dateStr + 'T00:00:00');
        return date.toLocaleDateString('en-AU', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        });
    }

    destroy() {
        if (this.tooltip) {
            document.body.removeChild(this.tooltip);
            this.tooltip = null;
        }
        
        window.removeEventListener('resize', this.handleResize.bind(this));
        
        if (this.container) {
            this.container.innerHTML = '';
        }
    }
}

// Export for use in other scripts
window.BookingChart = BookingChart;
