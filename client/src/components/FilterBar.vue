<template>
  <div class="filters-bar">
    <div class="filters-container">
      <div class="filters-grid">
        <select v-model="selectedPeriod" class="filter-select">
          <option value="all">{{ t('filters.allMonths') }}</option>
          <option value="2025-01">{{ t('months.january') }}</option>
          <option value="2025-02">{{ t('months.february') }}</option>
          <option value="2025-03">{{ t('months.march') }}</option>
          <option value="2025-04">{{ t('months.april') }}</option>
          <option value="2025-05">{{ t('months.may') }}</option>
          <option value="2025-06">{{ t('months.june') }}</option>
          <option value="2025-07">{{ t('months.july') }}</option>
          <option value="2025-08">{{ t('months.august') }}</option>
          <option value="2025-09">{{ t('months.september') }}</option>
          <option value="2025-10">{{ t('months.october') }}</option>
          <option value="2025-11">{{ t('months.november') }}</option>
          <option value="2025-12">{{ t('months.december') }}</option>
        </select>

        <select v-model="selectedLocation" class="filter-select">
          <option value="all">{{ t('filters.all') }}</option>
          <option value="San Francisco">{{ t('warehouses.sanFrancisco') }}</option>
          <option value="London">{{ t('warehouses.london') }}</option>
          <option value="Tokyo">{{ t('warehouses.tokyo') }}</option>
        </select>

        <select v-model="selectedCategory" class="filter-select">
          <option value="all">{{ t('filters.all') }}</option>
          <option value="circuit boards">{{ t('categories.circuitBoards') }}</option>
          <option value="sensors">{{ t('categories.sensors') }}</option>
          <option value="actuators">{{ t('categories.actuators') }}</option>
          <option value="controllers">{{ t('categories.controllers') }}</option>
          <option value="power supplies">{{ t('categories.powerSupplies') }}</option>
        </select>

        <select v-model="selectedStatus" class="filter-select">
          <option value="all">{{ t('filters.all') }}</option>
          <option value="delivered">{{ t('status.delivered') }}</option>
          <option value="shipped">{{ t('status.shipped') }}</option>
          <option value="processing">{{ t('status.processing') }}</option>
          <option value="backordered">{{ t('status.backordered') }}</option>
        </select>
      </div>

      <button
        class="reset-filters-btn"
        @click="resetFilters"
        :disabled="!hasActiveFilters"
        title="Reset all filters"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd" />
        </svg>
      </button>
    </div>
  </div>
</template>

<script>
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'FilterBar',
  setup() {
    const {
      selectedPeriod,
      selectedLocation,
      selectedCategory,
      selectedStatus,
      hasActiveFilters,
      resetFilters
    } = useFilters()

    const { t } = useI18n()

    return {
      t,
      selectedPeriod,
      selectedLocation,
      selectedCategory,
      selectedStatus,
      hasActiveFilters,
      resetFilters
    }
  }
}
</script>

<style scoped>
.filters-bar {
  background: #ffffff;
  border-bottom: 1px solid #e2e8f0;
  padding: 0.5rem 0;
}

.filters-container {
  padding: 0 2rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.filters-grid {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex: 1;
  flex-wrap: wrap;
}

.filter-select {
  padding: 0.3rem 0.625rem;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 0.75rem;
  color: #334155;
  background: #f8fafc;
  cursor: pointer;
  transition: border-color 0.15s ease, background 0.15s ease;
  font-weight: 500;
  font-family: inherit;
  appearance: auto;
}

.filter-select:hover {
  border-color: #cbd5e1;
  background: #ffffff;
}

.filter-select:focus {
  outline: none;
  border-color: #3b82f6;
  background: #ffffff;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1);
}

.reset-filters-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.3rem;
  background: transparent;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  color: #94a3b8;
  cursor: pointer;
  transition: all 0.15s ease;
  flex-shrink: 0;
}

.reset-filters-btn:hover:not(:disabled) {
  background: #f1f5f9;
  border-color: #cbd5e1;
  color: #475569;
}

.reset-filters-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.reset-filters-btn svg {
  width: 14px;
  height: 14px;
}
</style>
