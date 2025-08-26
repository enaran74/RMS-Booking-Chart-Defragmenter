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

        // Chart grid (always visible since category name is already shown above)
        const gridDiv = document.createElement('div');
        gridDiv.className = 'chart-grid show'; // Add 'show' class to make it visible by default
        gridDiv.id = `chart-${index}`;

        if (category.units && category.units.length > 0) {
            const scroller = this.createChartTable(category);
            gridDiv.appendChild(scroller);
        } else {
            gridDiv.innerHTML = '<div class="chart-no-data">No units found for this category</div>';
        }

        categoryDiv.appendChild(gridDiv);

        return categoryDiv;
    }

    createChartTable(category) {
        // Create a dedicated scroller so only the chart area scrolls horizontally
        const scroller = document.createElement('div');
        scroller.className = 'chart-scroller';

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
            // Parse as UTC and display as-is (backend already provides correct AEST dates)
            const [year, month, day] = dateStr.split('-');
            const date = new Date(parseInt(year), parseInt(month) - 1, parseInt(day)); // Local date object
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
        
        // Debug: print units rendered for this category
        try {
            const unitCodes = (category.units || []).map(u => u.unit_code);
        } catch (e) {}

        category.units.forEach(unit => {
            const row = this.createUnitRow(unit);
            tbody.appendChild(row);
        });

        table.appendChild(tbody);

        scroller.appendChild(table);
        return scroller;
    }

    createUnitRow(unit) {
        const row = document.createElement('tr');

        // Unit name cell
        const unitCell = document.createElement('td');
        unitCell.className = 'chart-unit-cell';
        unitCell.textContent = unit.unit_code;
        // Always show full unit name on hover, especially useful if truncated
        unitCell.title = `Full Unit: ${unit.unit_code}`;
        row.appendChild(unitCell);

        // Create booking spans for this unit
        this.createBookingSpansForRow(row, unit.bookings);

        return row;
    }

    createBookingSpansForRow(row, bookings) {
        // Create a lookup of date to booking for this unit
        const bookingLookup = this.createBookingLookup(bookings);
        
        // Track which dates we've already processed (to avoid duplicating spans)
        const processedDates = new Set();
        
        // Iterate through each date in the chart range
        this.chartData.date_range.forEach(dateStr => {
            if (processedDates.has(dateStr)) {
                return; // Skip dates already processed as part of a span
            }
            
            const booking = bookingLookup[dateStr];
            
            if (booking) {
                
                // Find the span length for this booking
                const spanInfo = this.calculateBookingSpan(dateStr, booking, bookingLookup);
                
                // Create a cell with appropriate colspan
                const cell = document.createElement('td');
                cell.className = 'chart-booking-cell';
                cell.colSpan = spanInfo.colspan;
                
                // Render booking content and styling
                this.renderBookingCell(cell, booking, dateStr, spanInfo);
                
                // Mark all dates in this span as processed
                const startIndex = this.chartData.date_range.indexOf(dateStr);
                for (let i = 0; i < spanInfo.colspan && (startIndex + i) < this.chartData.date_range.length; i++) {
                    const spanDate = this.chartData.date_range[startIndex + i];
                    processedDates.add(spanDate);
                }
                
                row.appendChild(cell);
            } else {
                // Empty cell
                const cell = document.createElement('td');
                cell.className = 'chart-booking-cell empty';
                cell.colSpan = 1;
                row.appendChild(cell);
                processedDates.add(dateStr);
            }
        });
    }

    calculateBookingSpan(startDateStr, booking, bookingLookup) {
        let colspan = 1;
        const startIndex = this.chartData.date_range.indexOf(startDateStr);
        
        // Safety check
        if (startIndex === -1) {
            return { colspan: 1, isStart: true, isEnd: true };
        }
        
        // Count consecutive days for the same booking (with safety limit)
        const maxSpan = this.chartData.date_range.length - startIndex;
        for (let i = 1; i < maxSpan; i++) {
            const nextDateIndex = startIndex + i;
            if (nextDateIndex >= this.chartData.date_range.length) {
                break; // Reached end of chart range
            }
            
            const nextDate = this.chartData.date_range[nextDateIndex];
            const nextBooking = bookingLookup[nextDate];
            
            // Check if next date has the same booking
            if (nextBooking && nextBooking.reservation_no === booking.reservation_no) {
                colspan++;
            } else {
                break; // Different booking or no booking
            }
        }
        
        return {
            colspan: colspan,
            isStart: true,
            isEnd: true
        };
    }

    addDaysToDate(dateStr, days) {
        const [year, month, day] = dateStr.split('-');
        const date = new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
        date.setDate(date.getDate() + days);
        // Safe YYYY-MM-DD without UTC conversion
        const yyyy = date.getFullYear();
        const mm = String(date.getMonth() + 1).padStart(2, '0');
        const dd = String(date.getDate()).padStart(2, '0');
        return `${yyyy}-${mm}-${dd}`;
    }

    createBookingLookup(bookings) {
        const lookup = {};
        
        bookings.forEach(booking => {
            const [startYear, startMonth, startDay] = booking.start_date.split('-');
            const [endYear, endMonth, endDay] = booking.end_date.split('-');
            const startDate = new Date(parseInt(startYear), parseInt(startMonth) - 1, parseInt(startDay));
            // Backend provides end_date as INCLUSIVE last occupied night.
            // Convert to exclusive end by adding one day so single-night stays render.
            const inclusiveEnd = new Date(parseInt(endYear), parseInt(endMonth) - 1, parseInt(endDay));
            const endDate = new Date(inclusiveEnd);
            endDate.setDate(endDate.getDate() + 1);
            
            let currentDate = new Date(startDate);
            // Hotel logic: guest occupies from check-in date until (but not including) check-out date
            while (currentDate < endDate) {
                const yyyy = currentDate.getFullYear();
                const mm = String(currentDate.getMonth() + 1).padStart(2, '0');
                const dd = String(currentDate.getDate()).padStart(2, '0');
                const dateStr = `${yyyy}-${mm}-${dd}`;
                lookup[dateStr] = booking;
                currentDate.setDate(currentDate.getDate() + 1);
            }
        });

        return lookup;
    }

    renderBookingCell(cell, booking, dateStr, spanInfo = null) {
        // Add status-based styling
        cell.classList.add(booking.color_class);
        
        // Add booking span classes
        if (spanInfo && spanInfo.colspan === 1) {
            cell.classList.add('booking-span-single');
        } else {
            cell.classList.add('booking-span');
            // For merged cells, always mark as start and end since it represents the full span
            cell.classList.add('booking-span-start');
            cell.classList.add('booking-span-end');
        }

        // Add move suggestion styling with direction arrow
        if (booking.is_move_suggestion) {
            cell.classList.add('move-suggestion');
        }

        // Add fixed booking styling
        if (booking.is_fixed) {
            cell.classList.add('fixed-booking');
        }

        // Set cell content with appropriate text for different booking types
        let cellContent = booking.guest_name;
        
        // Handle special booking statuses (matching CLI behavior)
        if (!booking.guest_name || booking.guest_name.trim() === '') {
            if (booking.status === 'Maintenance') {
                cellContent = 'Out Of Order'; // Display "Out Of Order" for maintenance bookings
            } else if (booking.status === 'Pencil') {
                cellContent = 'Pencil';
            } else {
                cellContent = 'Unknown';
            }
        }
        
                        // Add move suggestion arrow if applicable (only on first cell of span)
                if (booking.is_move_suggestion && spanInfo && spanInfo.isStart) {
                    const arrow = this.getMoveDirectionArrow(booking);
                    if (arrow) {
                        cellContent = `${arrow} ${cellContent}`; // Arrow prefix for move suggestions (like CLI Excel)
                        // Ensure left alignment for arrow
                        cell.style.textAlign = 'left';
                        cell.style.paddingLeft = '4px';
                    }
                }
        
        // Add fixed icon if applicable (only on first cell of span)
        if (booking.is_fixed && spanInfo && spanInfo.isStart) {
            cellContent = `🎯 ${cellContent}`; // Dart icon prefix for fixed bookings (like CLI Excel)
        }
        
        cell.textContent = cellContent;
        
        // Ensure proper alignment for fixed booking icons
        if (booking.is_fixed && spanInfo && spanInfo.isStart) {
                                cell.style.textAlign = 'left';
                    cell.style.verticalAlign = 'middle';
                    cell.style.paddingLeft = '4px';
        }

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
        const [year, month, day] = dateStr.split('-');
        const date = new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
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

    getMoveDirectionArrow(booking) {
        // Get directional arrow icon based on move direction (matching CLI logic)
        if (!booking.target_unit || !this.chartData) {
            return ""; // No arrow if missing data
        }

        // Normalize unit names (remove extra spaces)
        const normalizeUnit = (unitName) => unitName ? unitName.replace(/\s+/g, ' ').trim() : '';
        const normalizedCurrent = normalizeUnit(booking.current_unit);
        const normalizedTarget = normalizeUnit(booking.target_unit);

        // Find current unit's position in the chart
        let currentUnitPosition = -1;
        let targetUnitPosition = -1;
        
        // Search through ALL chart categories to find the units and their positions
        // (Move suggestions can involve units from any category, not just the displayed one)
        let unitIndex = 0;
        let foundCurrentMatch = false;
        let foundTargetMatch = false;
        
        for (const category of this.chartData.categories || []) {
            for (const unit of category.units || []) {
                            // Handle different unit data structures
            let unitName;
            if (typeof unit === 'string') {
                unitName = unit;
            } else if (unit && unit.unit_code) {
                unitName = unit.unit_code;
            } else if (unit && unit.unit_name) {
                unitName = unit.unit_name;
            } else if (unit && unit.name) {
                unitName = unit.name;
            } else {
                unitName = String(unit);
            }
                
                const normalizedChartUnit = normalizeUnit(unitName);
                
                if (normalizedChartUnit === normalizedCurrent) {
                    currentUnitPosition = unitIndex;
                    foundCurrentMatch = true;
                }
                if (normalizedChartUnit === normalizedTarget) {
                    targetUnitPosition = unitIndex;
                    foundTargetMatch = true;
                }
                unitIndex++;
            }
        }
        
        // Determine arrow direction based on positions
        if (currentUnitPosition === -1 || targetUnitPosition === -1) {
            return ""; // No arrow if units not found
        }
        
        if (targetUnitPosition < currentUnitPosition) {
            return "⬆️"; // Moving up in the chart
        } else {
            return "⬇️"; // Moving down in the chart (remove same position case as you requested)
        }
    }
}

// Export for use in other scripts
window.BookingChart = BookingChart;
