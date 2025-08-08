#!/usr/bin/env python3
"""
Defragmentation Analyzer
Core logic for analyzing reservation fragmentation and suggesting moves
"""

import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Optional, Tuple
import sys
from utils import get_logger

class DefragmentationAnalyzer:
    def __init__(self):
        """Initialize the defragmentation analyzer"""
        self.logger = get_logger()
        self.logger.debug("DefragmentationAnalyzer initialized")

    def analyze_defragmentation(self, reservations_df: pd.DataFrame, inventory_df: pd.DataFrame, 
                              constraint_start_date, constraint_end_date) -> List[Dict]:
        """Perform defragmentation analysis on live data"""
        start_time = time.time()
        self.logger.log_function_entry("analyze_defragmentation", 
                                     reservations_count=len(reservations_df),
                                     inventory_count=len(inventory_df),
                                     constraint_start=constraint_start_date,
                                     constraint_end=constraint_end_date)
        
        print(f"\n🔍 ANALYZING DEFRAGMENTATION OPPORTUNITIES")
        print("=" * 50)
        print(f"📊 Data: {len(reservations_df)} reservations, {len(inventory_df)} units")
        print(f"📅 Constraint Period: {constraint_start_date} to {constraint_end_date}")
        
        self.logger.info(f"Starting defragmentation analysis: {len(reservations_df)} reservations, {len(inventory_df)} units")
        
        suggestions = self._suggest_moves(reservations_df, inventory_df, constraint_start_date, constraint_end_date)
        
        duration = time.time() - start_time
        self.logger.log_performance_metric("Defragmentation analysis", duration)
        self.logger.log_data_summary("Move suggestions generated", len(suggestions))
        
        if suggestions:
            print(f"🎯 Generated {len(suggestions)} move suggestions")
        else:
            print("✅ No beneficial moves found - reservations are already optimized!")
            
        self.logger.log_function_exit("analyze_defragmentation", len(suggestions))
        return suggestions
    
    def _suggest_moves(self, reservations_df: pd.DataFrame, inventory_df: pd.DataFrame, 
                      constraint_start_date, constraint_end_date) -> List[Dict]:
        """Core defragmentation algorithm"""
        start_time = time.time()
        self.logger.log_function_entry("_suggest_moves")
        
        print("🔨 Building occupancy matrix...")
        self.logger.info("Building occupancy matrix")
        occupancy, dates, units_by_category = self._calculate_occupancy_matrix(
            reservations_df, inventory_df, constraint_start_date, constraint_end_date
        )
        
        # Calculate strategic importance for each category
        print("🎯 Calculating strategic importance for categories...")
        self.logger.info("Calculating strategic importance for categories")
        category_importance = self.calculate_category_strategic_importance(
            reservations_df, inventory_df, constraint_start_date, constraint_end_date
        )
        
        # Count fixed reservations
        fixed_count = sum(1 for _, res in reservations_df.iterrows() if self._is_reservation_fixed(res))
        total_reservations = len(reservations_df)
        
        self.logger.log_data_summary("Fixed reservations", fixed_count, f"out of {total_reservations} total")
        print(f"🔒 Fixed reservations: {fixed_count}/{total_reservations} (excluded from moves)")
        
        suggestions = []
        total_categories = len([cat for cat, units in units_by_category.items() if len(units) > 1])
        processed_categories = 0
        
        self.logger.log_data_summary("Categories to analyze", total_categories)
        print(f"🔄 Analyzing {total_categories} categories for optimization...")
        
        applied_moves = {}
        category_move_counters = {}  # Track move count per category
        categories_with_moves = []  # Track categories that actually have moves
        total_rejected_moves = 0  # Track total rejected moves
        skipped_categories = []  # Track categories that were skipped
        
        # Get sorted category order to match Excel chart display
        sorted_categories = sorted(units_by_category.keys())
        
        # First pass: collect all moves without assigning sequential order
        all_moves = []
        
        for category, units in units_by_category.items():
            if len(units) <= 1:
                self.logger.debug(f"Skipping {category} - only {len(units)} unit(s)")
                continue
            
            # Check strategic importance - skip categories with zero importance
            strategic_importance = category_importance.get(category, 0.0)
            if strategic_importance == 0.0:
                skipped_categories.append(category)
                self.logger.debug(f"Skipping {category} - strategic importance is 0.0")
                continue
                
            processed_categories += 1
            category_suggestions_start = len(suggestions)
            
            # Sequential optimization within category
            iteration = 0
            max_iterations = 20
            
            while iteration < max_iterations:
                iteration += 1
                found_improvement = False
                
                # Show progress for this iteration
                self._print_category_progress(iteration, max_iterations, category, processed_categories, total_categories)
                
                # Get moveable reservations
                moveable_reservations = self._get_moveable_reservations(
                    reservations_df, category, applied_moves, constraint_start_date, constraint_end_date
                )
                
                if not moveable_reservations:
                    # Complete the progress bar if no more moveable reservations
                    self._print_category_progress(max_iterations, max_iterations, category, processed_categories, total_categories)
                    break
                
                # Calculate current state
                current_occupancy = self._apply_moves_to_occupancy(
                    occupancy, applied_moves, reservations_df, constraint_start_date, constraint_end_date
                )
                current_score = self._calculate_fragmentation_score(category, units, dates, current_occupancy)
                
                # Find best move
                best_move, rejected_count = self._find_best_move(moveable_reservations, units, dates, current_occupancy, current_score, constraint_end_date)
                total_rejected_moves += rejected_count
                
                if best_move and best_move['improvement'] > 0:
                    found_improvement = True
                    res_info = best_move['res_info']
                    target_unit = best_move['target_unit']
                    
                    # Apply the move
                    applied_moves[res_info['res_no']] = target_unit
                    
                    # Initialize category counter if not exists
                    if category not in category_move_counters:
                        category_move_counters[category] = 0
                        # Add category to list of categories with moves
                        if category not in categories_with_moves:
                            categories_with_moves.append(category)
                    
                    # Increment category counter
                    category_move_counters[category] += 1
                    
                    # Create suggestion record without sequential order (will be assigned later)
                    suggestion = {
                        'Reservation_No': res_info['res_no'],
                        'Surname': res_info['surname'],
                        'Current_Unit': res_info['current_unit'],
                        'Suggested_Unit': target_unit,
                        'Category': category,
                        'Status': res_info['status'],
                        'Arrive_Date': res_info['arrive'].strftime('%d/%m/%Y'),
                        'Depart_Date': res_info['depart'].strftime('%d/%m/%Y'),
                        'Nights': res_info['nights'],
                        'Improvement_Score': round(best_move['improvement'], 2),
                        'Sequential_Order': '',  # Will be assigned after sorting
                        'Reason': f'Frees up {best_move["nights_freed"]} contiguous nights in {res_info["current_unit"]}'
                    }
                    all_moves.append(suggestion)
                
                if not found_improvement:
                    # Complete the progress bar when no more improvements found
                    self._print_category_progress(max_iterations, max_iterations, category, processed_categories, total_categories)
                    break
            
            # Category summary
            category_moves = len(all_moves) - category_suggestions_start
            self.logger.log_move_analysis(category, category_moves, 0)  # rejected_count not available here
            print(f"Found {category_moves} optimization moves for {category}")
        
        duration = time.time() - start_time
        self.logger.log_performance_metric("Move suggestions generation", duration)
        self.logger.log_data_summary("Total moves identified", len(all_moves))
        self.logger.log_data_summary("Categories with moves", len(categories_with_moves))
        self.logger.log_data_summary("Categories skipped", len(skipped_categories))
        
        print(f"\n✅ Sequential analysis complete: {len(all_moves)} moves identified")
        if total_rejected_moves > 0:
            print(f"❌ Rejected {total_rejected_moves} move suggestions as these would reduce contiguous availability")
        if skipped_categories:
            print(f"⏭️  Skipped {len(skipped_categories)} categories with sufficient contiguous availability")
        
        # Sort moves to match the chart order (by category)
        def sort_key(move):
            category = move['Category']
            return sorted_categories.index(category)
        
        all_moves.sort(key=sort_key)
        
        # Now assign sequential order based on sorted chart order
        categories_with_moves_sorted = [cat for cat in sorted_categories if cat in categories_with_moves]
        category_move_counters_final = {}
        
        for move in all_moves:
            category = move['Category']
            category_number = categories_with_moves_sorted.index(category) + 1  # 1-based indexing
            
            if category not in category_move_counters_final:
                category_move_counters_final[category] = 0
            category_move_counters_final[category] += 1
            
            move_number = category_move_counters_final[category]
            move['Sequential_Order'] = f"{category_number}.{move_number}"
        
        suggestions = all_moves
        self.logger.log_function_exit("_suggest_moves", len(suggestions))
        return suggestions
    
    def _calculate_occupancy_matrix(self, reservations_df: pd.DataFrame, inventory_df: pd.DataFrame, 
                                  constraint_start_date, constraint_end_date):
        """Calculate occupancy matrix showing unit availability"""
        
        # Group units by category
        units_by_category = defaultdict(list)
        for _, row in inventory_df.iterrows():
            units_by_category[row['Category']].append(row['Unit/Site'])
        
        # Generate date range
        date_range = []
        current = constraint_start_date
        while current <= constraint_end_date:
            date_range.append(current)
            current += timedelta(days=1)
        
        occupancy = {}
        
        # Process reservations
        for _, res in reservations_df.iterrows():
            arrive_date = self._parse_date(res['Arrive'])
            depart_date = self._parse_date(res['Depart'])
            unit = res['Unit/Site']
            is_fixed = self._is_reservation_fixed(res)
            
            if arrive_date and depart_date:
                effective_arrive = max(arrive_date, constraint_start_date)
                effective_depart = min(depart_date, constraint_end_date + timedelta(days=1))
                
                if effective_arrive < effective_depart:
                    current_date = effective_arrive
                    while current_date < effective_depart and current_date <= constraint_end_date:
                        occupancy[(unit, current_date)] = {
                            'res_no': res['Res No'],
                            'surname': res['Surname'],
                            'status': res['Status'],
                            'category': res['Category'],
                            'arrive': arrive_date,
                            'depart': depart_date,
                            'nights': res['Nights'],
                            'fixed': is_fixed
                        }
                        current_date += timedelta(days=1)
        
        return occupancy, set(date_range), units_by_category
    
    def _get_moveable_reservations(self, reservations_df: pd.DataFrame, category: str, applied_moves: dict, 
                                 constraint_start_date, constraint_end_date) -> List[Dict]:
        """Get reservations that can be moved within category"""
        moveable = []
        
        for _, res in reservations_df.iterrows():
            if (res['Category'] == category and 
                res['Status'] in ['Confirmed', 'Unconfirmed'] and
                not self._is_reservation_fixed(res)):
                
                arrive_date = self._parse_date(res['Arrive'])
                depart_date = self._parse_date(res['Depart'])
                
                # Only move reservations entirely within constraint period
                if (arrive_date and depart_date and 
                    arrive_date >= constraint_start_date and 
                    depart_date <= constraint_end_date + timedelta(days=1)):
                    
                    current_unit = applied_moves.get(res['Res No'], res['Unit/Site'])
                    
                    res_info = {
                        'res_no': res['Res No'],
                        'surname': res['Surname'],
                        'status': res['Status'],
                        'category': res['Category'],
                        'current_unit': current_unit,
                        'original_unit': res['Unit/Site'],
                        'arrive': arrive_date,
                        'depart': depart_date,
                        'nights': res['Nights'],
                        'fixed': self._is_reservation_fixed(res)
                    }
                    moveable.append(res_info)
        
        return moveable
    
    def _find_best_move(self, moveable_reservations: List[Dict], units: List[str], dates: set, 
                       current_occupancy: dict, current_score: float, constraint_end_date) -> Tuple[Optional[Dict], int]:
        """Find the best move for current iteration"""
        
        best_move = None
        best_improvement = 0
        rejected_count = 0
        
        for res in moveable_reservations:
            current_unit = res['current_unit']
            
            for target_unit in units:
                if target_unit == current_unit:
                    continue
                

                
                if self._can_move_reservation(res, target_unit, dates, current_occupancy, constraint_end_date):
                    # Calculate improvement
                    temp_occupancy = self._simulate_move(current_occupancy, res, target_unit, constraint_end_date)
                    new_score = self._calculate_fragmentation_score(res['category'], units, dates, temp_occupancy)
                    
                    # Validate that the move doesn't reduce contiguous availability
                    validation_result = self._validate_move_improves_contiguous_availability(res, current_unit, target_unit, 
                                                                         current_occupancy, dates, constraint_end_date, units)
                    
                    if not validation_result:
                        rejected_count += 1
                        continue
                        
                    if new_score > current_score:
                            improvement = new_score - current_score
                            nights_freed = self._calculate_contiguous_nights_freed(res, current_occupancy, dates, constraint_end_date)
                            
                            if improvement > best_improvement:
                                best_improvement = improvement
                                best_move = {
                                    'res_info': res,
                                    'target_unit': target_unit,
                                    'improvement': improvement,
                                    'nights_freed': nights_freed
                                }
        
        return best_move, rejected_count
    
    def _can_move_reservation(self, res_info: Dict, target_unit: str, dates: set, 
                            occupancy: dict, constraint_end_date) -> bool:
        """Check if reservation can be moved to target unit"""
        arrive_date = res_info['arrive']
        depart_date = res_info['depart']
        
        current_date = arrive_date
        while current_date < depart_date and current_date <= constraint_end_date:
            if (target_unit, current_date) in occupancy:
                return False
            current_date += timedelta(days=1)
        
        return True
    
    def _simulate_move(self, occupancy: dict, res_info: Dict, target_unit: str, constraint_end_date) -> dict:
        """Simulate moving a reservation to see the effect"""
        temp_occupancy = occupancy.copy()
        
        # Remove from current unit
        current_date = res_info['arrive']
        while current_date < res_info['depart'] and current_date <= constraint_end_date:
            key = (res_info['current_unit'], current_date)
            if key in temp_occupancy:
                del temp_occupancy[key]
            current_date += timedelta(days=1)
        
        # Add to target unit
        current_date = res_info['arrive']
        while current_date < res_info['depart'] and current_date <= constraint_end_date:
            temp_occupancy[(target_unit, current_date)] = {
                'res_no': res_info['res_no'],
                'surname': res_info['surname'],
                'status': res_info['status'],
                'category': res_info['category'],
                'arrive': res_info['arrive'],
                'depart': res_info['depart'],
                'nights': res_info['nights'],
                'fixed': res_info['fixed']
            }
            current_date += timedelta(days=1)
        
        return temp_occupancy
    
    def _calculate_fragmentation_score(self, category: str, units: List[str], dates: set, occupancy: dict) -> float:
        """Calculate fragmentation score for category - lower is better (less fragmented)"""
        total_gaps = 0
        total_available_days = 0
        max_contiguous_period = 0
        strategic_value = 0
        
        for unit in units:
            available_periods = self._find_contiguous_availability(unit, dates, occupancy)
            for start, end, days in available_periods:
                total_available_days += days
                if days > 0:
                    total_gaps += 1
                    max_contiguous_period = max(max_contiguous_period, days)
                    # Strategic value: longer contiguous periods are exponentially more valuable
                    strategic_value += days * days  # Quadratic scoring for contiguous periods
        
        if total_gaps == 0:
            return 0
        
        # New scoring: penalize fragmentation, reward strategic value
        # Lower score = better (less fragmented)
        fragmentation_penalty = total_gaps * 10  # Penalty for having many small gaps
        strategic_bonus = strategic_value / 100  # Bonus for long contiguous periods
        
        return fragmentation_penalty - strategic_bonus
    
    def _find_contiguous_availability(self, unit: str, dates: set, occupancy: dict) -> List[tuple]:
        """Find contiguous available periods for a unit"""
        available_periods = []
        current_start = None
        
        for date in sorted(dates):
            if (unit, date) not in occupancy:
                if current_start is None:
                    current_start = date
            else:
                if current_start is not None:
                    days = (date - current_start).days
                    available_periods.append((current_start, date, days))
                    current_start = None
        
        # Handle period extending to end
        if current_start is not None:
            end_date = max(dates) + timedelta(days=1)
            days = (end_date - current_start).days
            available_periods.append((current_start, end_date, days))
        
        return available_periods
    
    def _calculate_contiguous_nights_freed(self, res_info: Dict, occupancy: dict, dates: set, constraint_end_date) -> int:
        """Calculate nights freed in original unit"""
        current_unit = res_info['current_unit']
        arrive_date = res_info['arrive']
        depart_date = res_info['depart']
        
        # Remove the reservation temporarily
        temp_occupancy = occupancy.copy()
        current_date = arrive_date
        while current_date < depart_date and current_date <= constraint_end_date:
            key = (current_unit, current_date)
            if key in temp_occupancy:
                del temp_occupancy[key]
            current_date += timedelta(days=1)
        
        # Find contiguous periods
        available_periods = self._find_contiguous_availability(current_unit, dates, temp_occupancy)
        
        # Find the period that would include the freed dates
        max_freed = 0
        reservation_dates = set()
        current_date = arrive_date
        while current_date < depart_date and current_date <= constraint_end_date:
            reservation_dates.add(current_date)
            current_date += timedelta(days=1)
        
        for start_date, end_date, period_length in available_periods:
            period_dates = set()
            current = start_date
            while current < end_date:
                period_dates.add(current)
                current += timedelta(days=1)
            
            if reservation_dates.intersection(period_dates):
                max_freed = max(max_freed, period_length)
        
        return max_freed
    
    def _validate_move_improves_contiguous_availability(self, res_info: Dict, current_unit: str, target_unit: str,
                                                      occupancy: dict, dates: set, constraint_end_date, units: List[str]) -> bool:
        """Validate that a move improves contiguous availability rather than reducing it"""
        
        arrive_date = res_info['arrive']
        depart_date = res_info['depart']
        
        # Calculate current contiguous availability for the category
        current_contiguous_availability = self._calculate_category_contiguous_availability(
            res_info['category'], occupancy, dates, constraint_end_date, units
        )
        
        # Calculate current availability quality (longer periods are better)
        current_quality = self._calculate_availability_quality(
            res_info['category'], occupancy, dates, constraint_end_date, units
        )
        
        # Simulate the move
        temp_occupancy = self._simulate_move(occupancy, res_info, target_unit, constraint_end_date)
        
        # Calculate new contiguous availability
        new_contiguous_availability = self._calculate_category_contiguous_availability(
            res_info['category'], temp_occupancy, dates, constraint_end_date, units
        )
        
        # Calculate new availability quality
        new_quality = self._calculate_availability_quality(
            res_info['category'], temp_occupancy, dates, constraint_end_date, units
        )
        
        # Move is valid if it improves both total availability AND quality
        # Quality is more important than total availability
        if new_quality < current_quality:
            return False  # Reject moves that reduce quality
        
        # If quality is maintained or improved, then check total availability
        return new_contiguous_availability >= current_contiguous_availability
    
    def _calculate_category_contiguous_availability(self, category: str, occupancy: dict, dates: set, constraint_end_date, units: List[str]) -> int:
        """Calculate total contiguous availability for a category"""
        
        if not units:
            return 0
        
        total_contiguous_availability = 0
        
        for unit in units:
            available_periods = self._find_contiguous_availability(unit, dates, occupancy)
            for start, end, days in available_periods:
                total_contiguous_availability += days
        
        return total_contiguous_availability
    
    def _calculate_availability_quality(self, category: str, occupancy: dict, dates: set, constraint_end_date, units: List[str]) -> float:
        """Calculate the quality of availability (longer periods are better)"""
        
        if not units:
            return 0.0
        
        # Find all contiguous availability periods for each unit
        all_periods = []
        for unit in units:
            available_periods = self._find_contiguous_availability(unit, dates, occupancy)
            for start, end, days in available_periods:
                if days > 0:
                    all_periods.append(days)
        
        if not all_periods:
            return 0.0
        
        # Quality is based on:
        # 1. Average period length (longer is better)
        # 2. Maximum period length (longer is better)
        # 3. Number of periods (fewer is better - less fragmentation)
        
        avg_period_length = sum(all_periods) / len(all_periods)
        max_period_length = max(all_periods)
        num_periods = len(all_periods)
        
        # Quality score: prioritize longer periods and fewer gaps
        # Formula: (avg_length * 0.4) + (max_length * 0.4) + (1/num_periods * 0.2)
        quality_score = (avg_period_length * 0.4) + (max_period_length * 0.4) + ((1.0 / num_periods) * 20.0)
        
        return quality_score
    
    def _apply_moves_to_occupancy(self, original_occupancy: dict, applied_moves: dict, 
                                reservations_df: pd.DataFrame, constraint_start_date, constraint_end_date) -> dict:
        """Apply all moves to occupancy matrix"""
        new_occupancy = original_occupancy.copy()
        
        for res_no, new_unit in applied_moves.items():
            res_row = reservations_df[reservations_df['Res No'] == res_no]
            if res_row.empty:
                continue
                
            res = res_row.iloc[0]
            original_unit = res['Unit/Site']
            arrive_date = self._parse_date(res['Arrive'])
            depart_date = self._parse_date(res['Depart'])
            is_fixed = self._is_reservation_fixed(res)
            
            # Remove from original unit
            current_date = arrive_date
            while current_date < depart_date and current_date <= constraint_end_date:
                key = (original_unit, current_date)
                if key in new_occupancy:
                    del new_occupancy[key]
                current_date += timedelta(days=1)
            
            # Add to new unit
            current_date = arrive_date
            while current_date < depart_date and current_date <= constraint_end_date:
                new_occupancy[(new_unit, current_date)] = {
                    'res_no': res['Res No'],
                    'surname': res['Surname'],
                    'status': res['Status'],
                    'category': res['Category'],
                    'arrive': arrive_date,
                    'depart': depart_date,
                    'nights': res['Nights'],
                    'fixed': is_fixed
                }
                current_date += timedelta(days=1)
        
        return new_occupancy

    # UTILITY METHODS
    # ===============
    
    def _parse_date(self, date_str: str):
        """Parse date string in format 'DD/MM/YYYY HH:MM'"""
        try:
            return datetime.strptime(date_str.split()[0], '%d/%m/%Y').date()
        except:
            try:
                return datetime.strptime(date_str, '%d/%m/%Y').date()
            except:
                print(f"Warning: Could not parse date: {date_str}")
                return None
    
    def _is_reservation_fixed(self, reservation_row) -> bool:
        """Check if reservation is marked as fixed"""
        if 'Fixed' in reservation_row:
            fixed_value = reservation_row['Fixed']
            if isinstance(fixed_value, bool):
                return fixed_value
            elif isinstance(fixed_value, str):
                return fixed_value.lower() in ['true', '1', 'yes']
        return False
    
    def _print_category_progress(self, current: int, total: int, category_name: str, category_num: int, total_categories: int):
        """Print category-specific progress in clean format"""
        bar_length = 30
        progress = current / total if total > 0 else 1.0
        filled_length = int(bar_length * progress)
        bar = '█' * filled_length + '-' * (bar_length - filled_length)
        percent = progress * 100
        
        # Use the clean format: [Progress Bar] X% - Analyzing {category name} - X/X
        sys.stdout.write(f'\r[{bar}] {percent:5.1f}% - Analyzing {category_name} - {category_num}/{total_categories}')
        sys.stdout.flush()
        
        # Add newline when complete
        if current == total:
            print()
    
    def calculate_category_strategic_importance(self, reservations_df: pd.DataFrame, inventory_df: pd.DataFrame, 
                                             constraint_start_date, constraint_end_date) -> Dict[str, float]:
        """Calculate strategic importance score for each category based on fragmentation and availability patterns"""
        
        # Build occupancy matrix
        occupancy, dates, units_by_category = self._calculate_occupancy_matrix(
            reservations_df, inventory_df, constraint_start_date, constraint_end_date
        )
        
        category_importance = {}
        
        for category, units in units_by_category.items():
            if len(units) <= 1:
                category_importance[category] = 0.0
                continue
            
            # Calculate current contiguous availability patterns
            contiguous_availability_by_date = {}
            for date in dates:
                available_units = 0
                for unit in units:
                    if (unit, date) not in occupancy:
                        available_units += 1
                contiguous_availability_by_date[date] = available_units
            
            # Calculate strategic importance based on contiguous availability needs
            strategic_score = 0.0
            
            # Check if category already has sufficient contiguous availability
            # If we have 3+ units available on most dates, no strategic importance
            dates_with_sufficient_availability = 0
            total_dates = len(dates)
            
            for date, available_units in contiguous_availability_by_date.items():
                if available_units >= 3:  # Sufficient contiguous availability
                    dates_with_sufficient_availability += 1
            
            # If most dates have sufficient availability, low strategic importance
            if dates_with_sufficient_availability / total_dates > 0.7:  # 70% threshold
                strategic_score = 0.0
            else:
                # Calculate fragmentation-based importance
                total_gaps = 0
                total_available_days = 0
                avg_contiguous_length = 0
                
                for unit in units:
                    available_periods = self._find_contiguous_availability(unit, dates, occupancy)
                    for start, end, days in available_periods:
                        total_available_days += days
                        if days > 0:
                            total_gaps += 1
                
                if total_gaps > 0:
                    avg_contiguous_length = total_available_days / total_gaps
                
                # Strategic importance factors:
                # 1. Low average contiguous length = high importance (needs consolidation)
                # 2. High number of gaps = high importance (fragmented)
                # 3. Low availability density = high importance
                
                # Contiguous length factor: shorter periods need consolidation
                contiguous_factor = max(0, (7 - avg_contiguous_length) / 7)  # 0-1 scale, higher for shorter periods
                
                # Fragmentation factor: more gaps = higher importance
                fragmentation_factor = min(total_gaps / len(units), 3.0) / 3.0  # 0-1 scale, cap at 3 gaps per unit
                
                # Density factor: lower density = higher importance
                total_possible_days = len(units) * len(dates)
                availability_density = total_available_days / total_possible_days if total_possible_days > 0 else 0
                density_factor = 1 - availability_density
                
                # Combined strategic importance score (0-1 scale)
                strategic_score = (contiguous_factor * 0.5 + 
                                 fragmentation_factor * 0.3 + 
                                 density_factor * 0.2)
                
                # Normalize to 0-1 range
                strategic_score = min(max(strategic_score, 0.0), 1.0)
            
            category_importance[category] = strategic_score
        
        return category_importance
    
    def analyze_holiday_defragmentation(self, reservations_df: pd.DataFrame, inventory_df: pd.DataFrame,
                                      holiday_periods: List[Dict], constraint_start_date, constraint_end_date) -> List[Dict]:
        """
        Analyze defragmentation specifically for holiday periods
        
        Args:
            reservations_df: DataFrame of reservations
            inventory_df: DataFrame of inventory units
            holiday_periods: List of holiday period dictionaries
            constraint_start_date: Start date for analysis
            constraint_end_date: End date for analysis
            
        Returns:
            List of holiday-specific move suggestions
        """
        start_time = time.time()
        self.logger.log_function_entry("analyze_holiday_defragmentation", 
                                     reservations_count=len(reservations_df),
                                     inventory_count=len(inventory_df),
                                     holiday_periods_count=len(holiday_periods))
        
        print(f"\n🎄 ANALYZING HOLIDAY DEFRAGMENTATION OPPORTUNITIES")
        print("=" * 60)
        print(f"📊 Data: {len(reservations_df)} reservations, {len(inventory_df)} units")
        print(f"🎅 Holiday Periods: {len(holiday_periods)} periods")
        
        holiday_moves = []
        
        for i, holiday_period in enumerate(holiday_periods, 1):
            holiday_name = holiday_period['name']
            holiday_start = holiday_period['start_date']
            holiday_end = holiday_period['end_date']
            extended_start = holiday_period['extended_start']
            extended_end = holiday_period['extended_end']
            importance = holiday_period['importance']
            
            print(f"\n🎯 Analyzing Holiday {i}/{len(holiday_periods)}: {holiday_name}")
            print(f"   📅 Period: {holiday_start} to {holiday_end}")
            print(f"   📅 Extended: {extended_start} to {extended_end}")
            print(f"   ⭐ Importance: {importance}")
            
            # Filter reservations for this extended period
            holiday_reservations = self._filter_reservations_for_period(
                reservations_df, extended_start, extended_end
            )
            
            if len(holiday_reservations) == 0:
                print(f"   ⚠️  No reservations found for {holiday_name} period")
                continue
            
            print(f"   📋 Found {len(holiday_reservations)} reservations for analysis")
            
            # Run defragmentation analysis for this period
            period_moves = self._suggest_moves(
                holiday_reservations, inventory_df, extended_start, extended_end
            )
            
            # Add holiday metadata to moves
            for move in period_moves:
                move.update({
                    'holiday_period': holiday_name,
                    'holiday_type': holiday_period['type'],
                    'holiday_importance': importance,
                    'holiday_start_date': holiday_start,
                    'holiday_end_date': holiday_end,
                    'extended_start_date': extended_start,
                    'extended_end_date': extended_end,
                    'is_holiday_move': True,
                    'move_id': f"H{len(holiday_moves) + 1}.{move.get('move_id', '1')}"
                })
            
            holiday_moves.extend(period_moves)
            print(f"   ✅ Generated {len(period_moves)} moves for {holiday_name}")
        
        duration = time.time() - start_time
        self.logger.log_performance_metric("Holiday defragmentation analysis", duration)
        self.logger.log_data_summary("Holiday move suggestions generated", len(holiday_moves))
        
        if holiday_moves:
            print(f"\n🎄 Generated {len(holiday_moves)} total holiday move suggestions")
        else:
            print(f"\n✅ No holiday moves found - reservations are already optimized for holiday periods!")
        
        self.logger.log_function_exit("analyze_holiday_defragmentation", len(holiday_moves))
        return holiday_moves
    
    def analyze_holiday_defragmentation_2month_forward(self, reservations_df: pd.DataFrame, inventory_df: pd.DataFrame,
                                                     holiday_periods: List[Dict], regular_analysis_start_date, 
                                                     regular_analysis_end_date) -> List[Dict]:
        """
        Analyze defragmentation for holiday periods in a 2-month forward window
        This method focuses on early optimization for upcoming holidays
        
        Args:
            reservations_df: DataFrame of reservations
            inventory_df: DataFrame of inventory units
            holiday_periods: List of holiday period dictionaries (2-month forward)
            regular_analysis_start_date: Start date of regular analysis (for deduplication)
            regular_analysis_end_date: End date of regular analysis (for deduplication)
            
        Returns:
            List of holiday-specific move suggestions (avoiding duplicates with regular analysis)
        """
        start_time = time.time()
        self.logger.log_function_entry("analyze_holiday_defragmentation_2month_forward", 
                                     reservations_count=len(reservations_df),
                                     inventory_count=len(inventory_df),
                                     holiday_periods_count=len(holiday_periods))
        
        print(f"\n🎄 ANALYZING 2-MONTH FORWARD HOLIDAY DEFRAGMENTATION")
        print("=" * 70)
        print(f"📊 Data: {len(reservations_df)} reservations, {len(inventory_df)} units")
        print(f"🎅 Holiday Periods: {len(holiday_periods)} periods")
        print(f"📅 Regular Analysis Period: {regular_analysis_start_date} to {regular_analysis_end_date}")
        
        holiday_moves = []
        
        for i, holiday_period in enumerate(holiday_periods, 1):
            holiday_name = holiday_period['name']
            holiday_start = holiday_period['start_date']
            holiday_end = holiday_period['end_date']
            extended_start = holiday_period['extended_start']
            extended_end = holiday_period['extended_end']
            importance = holiday_period['importance']
            
            print(f"\n🎯 Analyzing Holiday {i}/{len(holiday_periods)}: {holiday_name}")
            print(f"   📅 Period: {holiday_start} to {holiday_end}")
            print(f"   📅 Extended: {extended_start} to {extended_end}")
            print(f"   ⭐ Importance: {importance}")
            
            # Check if this holiday period overlaps with regular analysis
            overlap_with_regular = (
                extended_start <= regular_analysis_end_date and 
                extended_end >= regular_analysis_start_date
            )
            
            if overlap_with_regular:
                print(f"   ⚠️  Holiday period overlaps with regular analysis - will deduplicate moves")
            
            # Filter reservations for this extended period
            holiday_reservations = self._filter_reservations_for_period(
                reservations_df, extended_start, extended_end
            )
            
            if len(holiday_reservations) == 0:
                print(f"   ⚠️  No reservations found for {holiday_name} period")
                continue
            
            print(f"   📋 Found {len(holiday_reservations)} reservations for analysis")
            
            # Run defragmentation analysis for this period
            period_moves = self._suggest_moves(
                holiday_reservations, inventory_df, extended_start, extended_end
            )
            
            # Add holiday metadata to moves
            for move in period_moves:
                move.update({
                    'holiday_period': holiday_name,
                    'holiday_type': holiday_period['type'],
                    'holiday_importance': importance,
                    'holiday_start_date': holiday_start,
                    'holiday_end_date': holiday_end,
                    'extended_start_date': extended_start,
                    'extended_end_date': extended_end,
                    'is_holiday_move': True,
                    'analysis_window': '2month_forward',
                    'overlaps_regular_analysis': overlap_with_regular,
                    'move_id': f"H2M{len(holiday_moves) + 1}.{move.get('move_id', '1')}"
                })
            
            holiday_moves.extend(period_moves)
            print(f"   ✅ Generated {len(period_moves)} moves for {holiday_name}")
        
        duration = time.time() - start_time
        self.logger.log_performance_metric("2-month forward holiday defragmentation analysis", duration)
        self.logger.log_data_summary("2-month forward holiday move suggestions generated", len(holiday_moves))
        
        if holiday_moves:
            print(f"\n🎄 Generated {len(holiday_moves)} total 2-month forward holiday move suggestions")
        else:
            print(f"\n✅ No 2-month forward holiday moves found!")
        
        self.logger.log_function_exit("analyze_holiday_defragmentation_2month_forward", len(holiday_moves))
        return holiday_moves
    
    def deduplicate_moves(self, regular_moves: List[Dict], holiday_moves: List[Dict]) -> List[Dict]:
        """
        Remove duplicate moves between regular and holiday analysis
        
        Args:
            regular_moves: List of regular move suggestions
            holiday_moves: List of holiday move suggestions
            
        Returns:
            List of deduplicated moves
        """
        self.logger.log_function_entry("deduplicate_moves", 
                                     regular_moves_count=len(regular_moves),
                                     holiday_moves_count=len(holiday_moves))
        
        print(f"\n🔄 DEDUPLICATING MOVES")
        print("=" * 40)
        print(f"📋 Regular moves: {len(regular_moves)}")
        print(f"🎄 Holiday moves: {len(holiday_moves)}")
        
        all_moves = regular_moves.copy()
        duplicates_found = 0
        overlapping_holiday_moves = 0
        
        for holiday_move in holiday_moves:
            # Check if this move already exists in regular moves
            is_duplicate = False
            overlaps_regular = holiday_move.get('overlaps_regular_analysis', False)
            
            if overlaps_regular:
                overlapping_holiday_moves += 1
                # More aggressive deduplication for overlapping periods
                for regular_move in regular_moves:
                    if self._are_moves_duplicate_enhanced(holiday_move, regular_move):
                        is_duplicate = True
                        duplicates_found += 1
                        self.logger.debug(f"Overlapping duplicate found: {holiday_move.get('move_id', 'Unknown')} matches {regular_move.get('move_id', 'Unknown')}")
                        break
            else:
                # Standard deduplication for non-overlapping periods
                for regular_move in regular_moves:
                    if self._are_moves_duplicate(holiday_move, regular_move):
                        is_duplicate = True
                        duplicates_found += 1
                        self.logger.debug(f"Duplicate found: {holiday_move.get('move_id', 'Unknown')} matches {regular_move.get('move_id', 'Unknown')}")
                        break
            
            if not is_duplicate:
                all_moves.append(holiday_move)
        
        print(f"🔄 Duplicates removed: {duplicates_found}")
        print(f"🎄 Overlapping holiday moves: {overlapping_holiday_moves}")
        print(f"📋 Final moves: {len(all_moves)}")
        
        self.logger.log_data_summary("Duplicates removed", duplicates_found)
        self.logger.log_data_summary("Overlapping holiday moves", overlapping_holiday_moves)
        self.logger.log_data_summary("Final moves after deduplication", len(all_moves))
        self.logger.log_function_exit("deduplicate_moves", len(all_moves))
        
        return all_moves
    
    def _are_moves_duplicate(self, move1: Dict, move2: Dict) -> bool:
        """
        Check if two moves are duplicates based on key attributes
        
        Args:
            move1: First move dictionary
            move2: Second move dictionary
            
        Returns:
            True if moves are duplicates, False otherwise
        """
        # Key attributes to compare for duplication
        key_attributes = [
            'property', 'from_unit', 'to_unit', 'from_date', 'to_date', 'guest_name'
        ]
        
        for attr in key_attributes:
            if move1.get(attr) != move2.get(attr):
                return False
        
        return True
    
    def _are_moves_duplicate_enhanced(self, holiday_move: Dict, regular_move: Dict) -> bool:
        """
        Enhanced duplicate detection for overlapping holiday and regular moves
        More aggressive deduplication to avoid suggesting the same move twice
        
        Args:
            holiday_move: Holiday move dictionary
            regular_move: Regular move dictionary
            
        Returns:
            True if moves are duplicates, False otherwise
        """
        # Basic attribute comparison
        basic_attributes = [
            'property', 'from_unit', 'to_unit', 'guest_name'
        ]
        
        for attr in basic_attributes:
            if holiday_move.get(attr) != regular_move.get(attr):
                return False
        
        # Enhanced date range comparison for overlapping periods
        holiday_start = holiday_move.get('from_date')
        holiday_end = holiday_move.get('to_date')
        regular_start = regular_move.get('from_date')
        regular_end = regular_move.get('to_date')
        
        if holiday_start and holiday_end and regular_start and regular_end:
            # Check if date ranges overlap significantly (more than 50% overlap)
            overlap_start = max(holiday_start, regular_start)
            overlap_end = min(holiday_end, regular_end)
            
            if overlap_start <= overlap_end:
                holiday_duration = (holiday_end - holiday_start).days
                overlap_duration = (overlap_end - overlap_start).days
                
                # If more than 50% overlap, consider it a duplicate
                if holiday_duration > 0 and (overlap_duration / holiday_duration) > 0.5:
                    return True
        
        return False
    
    def merge_move_lists(self, regular_moves: List[Dict], holiday_moves: List[Dict]) -> List[Dict]:
        """
        Merge regular and holiday moves with proper ordering
        
        Args:
            regular_moves: List of regular move suggestions
            holiday_moves: List of holiday move suggestions
            
        Returns:
            List of merged moves with holiday moves prioritized
        """
        self.logger.log_function_entry("merge_move_lists", 
                                     regular_moves_count=len(regular_moves),
                                     holiday_moves_count=len(holiday_moves))
        
        # First deduplicate
        deduplicated_moves = self.deduplicate_moves(regular_moves, holiday_moves)
        
        # Sort moves by priority: holiday moves first, then by improvement score
        def sort_key(move):
            # Holiday moves get priority
            is_holiday = move.get('is_holiday_move', False)
            importance = move.get('holiday_importance', 'Low')
            improvement_score = move.get('improvement_score', 0.0)
            
            # Priority order: Holiday High > Holiday Medium > Regular High Score > Regular Low Score
            if is_holiday and importance == 'High':
                return (0, 1.0 - improvement_score)  # High priority, then by score (descending)
            elif is_holiday and importance == 'Medium':
                return (1, 1.0 - improvement_score)  # Medium priority, then by score (descending)
            else:
                return (2, 1.0 - improvement_score)  # Regular priority, then by score (descending)
        
        sorted_moves = sorted(deduplicated_moves, key=sort_key)
        
        # Update move IDs to reflect new order
        holiday_count = 1
        regular_count = 1
        for move in sorted_moves:
            if move.get('is_holiday_move', False):
                move['move_id'] = f"H{holiday_count}"
                holiday_count += 1
            else:
                move['move_id'] = f"R{regular_count}"
                regular_count += 1
        
        self.logger.log_data_summary("Merged moves", len(sorted_moves))
        self.logger.log_function_exit("merge_move_lists", len(sorted_moves))
        
        return sorted_moves
    
    def calculate_holiday_importance_score(self, holiday_data: Dict) -> float:
        """
        Calculate importance score for holiday period
        
        Args:
            holiday_data: Holiday period data
            
        Returns:
            Importance score (0.0 to 1.0)
        """
        importance_mapping = {
            'High': 1.0,
            'Medium': 0.7,
            'Low': 0.4
        }
        
        importance = holiday_data.get('importance', 'Medium')
        return importance_mapping.get(importance, 0.5)
    
    def _filter_reservations_for_period(self, reservations_df: pd.DataFrame, 
                                      start_date, end_date) -> pd.DataFrame:
        """
        Filter reservations for a specific date period
        
        Args:
            reservations_df: DataFrame of reservations
            start_date: Start date for filtering
            end_date: End date for filtering
            
        Returns:
            Filtered DataFrame of reservations
        """
        filtered_reservations = []
        
        for _, reservation in reservations_df.iterrows():
            arrive_date = self._parse_date(reservation['Arrive'])
            depart_date = self._parse_date(reservation['Depart'])
            
            if arrive_date and depart_date:
                # Check if reservation overlaps with the period
                if (arrive_date <= end_date and depart_date >= start_date):
                    filtered_reservations.append(reservation)
        
        return pd.DataFrame(filtered_reservations) if filtered_reservations else pd.DataFrame()