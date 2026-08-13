<template>
  <div class="restocking-view">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p class="page-description">{{ t('restocking.description') }}</p>
    </div>

    <!-- Budget Controls Card -->
    <div class="card budget-card">
      <div class="card-header">
        <h3 class="card-title">{{ t('restocking.budget') }}</h3>
      </div>
      <div class="budget-controls">
        <div class="slider-row">
          <input
            type="range"
            min="0"
            max="500000"
            step="1000"
            v-model.number="budget"
            class="budget-slider"
          />
          <span class="budget-value">{{ formatCurrency(budget) }}</span>
        </div>
        <div class="budget-summary">
          <div class="budget-stat">
            <span class="budget-label">{{ t('restocking.budgetUsed') }}</span>
            <span class="budget-amount used">{{ formatCurrency(budgetUsed) }}</span>
          </div>
          <div class="budget-stat">
            <span class="budget-label">{{ t('restocking.budgetRemaining') }}</span>
            <span class="budget-amount remaining">{{ formatCurrency(budgetRemaining) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading / Error states -->
    <div v-if="loading" class="loading">Loading demand data...</div>
    <div v-else-if="error" class="error">{{ error }}</div>

    <!-- Success message -->
    <div v-if="orderSuccess" class="success-banner">
      {{ t('restocking.orderSuccess') }}
    </div>

    <!-- Recommended Items Card -->
    <div v-if="!loading && !error" class="card">
      <div class="card-header">
        <h3 class="card-title">{{ t('restocking.recommendedItems') }}</h3>
      </div>
      <div v-if="allocatedItems.length === 0" class="empty-state">
        {{ t('restocking.noItemsInBudget') }}
      </div>
      <div v-else class="table-container">
        <table>
          <thead>
            <tr>
              <th>{{ t('restocking.table.itemName') }}</th>
              <th>{{ t('restocking.table.sku') }}</th>
              <th>{{ t('restocking.table.trend') }}</th>
              <th class="text-right">{{ t('restocking.table.qtyToRestock') }}</th>
              <th class="text-right">{{ t('restocking.table.unitCost') }}</th>
              <th class="text-right">{{ t('restocking.table.subtotal') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in displayedItems" :key="item.item_sku" :class="{ 'qty-edited': quantityOverrides[item.item_sku] !== undefined }">
              <td>{{ item.item_name }}</td>
              <td class="sku-cell">{{ item.item_sku }}</td>
              <td><span :class="['badge', item.trend]">{{ item.trend }}</span></td>
              <td class="text-right qty-cell">
                <input
                  type="number"
                  class="qty-input"
                  :value="item.display_qty"
                  min="1"
                  @change="setOverride(item.item_sku, $event.target.value)"
                />
              </td>
              <td class="text-right">${{ item.unit_cost.toFixed(2) }}</td>
              <td class="text-right"><strong>${{ item.display_subtotal.toLocaleString(undefined, { maximumFractionDigits: 2 }) }}</strong></td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="place-order-row">
        <button
          class="place-order-btn"
          :disabled="allocatedItems.length === 0 || submitting"
          @click="placeOrder"
        >
          {{ submitting ? 'Placing Order...' : t('restocking.placeOrder') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Restocking',
  setup() {
    const { t } = useI18n()

    const budget = ref(50000)
    const allForecasts = ref([])
    const inventoryItems = ref([])
    const loading = ref(false)
    const submitting = ref(false)
    const orderSuccess = ref(false)
    const error = ref(null)
    const quantityOverrides = ref({})

    onMounted(async () => {
      loading.value = true
      try {
        const [forecasts, inventory] = await Promise.all([
          api.getDemandForecasts(),
          api.getInventory({})
        ])
        allForecasts.value = forecasts
        inventoryItems.value = inventory
      } catch (err) {
        error.value = 'Failed to load data.'
      } finally {
        loading.value = false
      }
    })

    // SKU → unit_cost lookup map
    const inventoryCostMap = computed(() => {
      const map = {}
      inventoryItems.value.forEach(item => { map[item.sku] = item.unit_cost })
      return map
    })

    // Priority-sorted forecasts (exclude "decreasing")
    const TREND_PRIORITY = { increasing: 0, stable: 1 }
    const prioritizedForecasts = computed(() =>
      allForecasts.value
        .filter(f => f.trend !== 'decreasing')
        .sort((a, b) => (TREND_PRIORITY[a.trend] ?? 99) - (TREND_PRIORITY[b.trend] ?? 99))
    )

    // Greedy budget allocation
    const allocatedItems = computed(() => {
      let remaining = budget.value
      const result = []
      for (const forecast of prioritizedForecasts.value) {
        if (remaining <= 0) break
        const unitCost = inventoryCostMap.value[forecast.item_sku]
        if (unitCost == null) continue
        const fullQty = forecast.forecasted_demand
        const fullCost = fullQty * unitCost
        if (fullCost <= remaining) {
          result.push({ ...forecast, unit_cost: unitCost, qty_to_restock: fullQty, subtotal: fullCost })
          remaining -= fullCost
        } else {
          const partialQty = Math.floor(remaining / unitCost)
          if (partialQty > 0) {
            result.push({ ...forecast, unit_cost: unitCost, qty_to_restock: partialQty, subtotal: partialQty * unitCost })
            remaining -= partialQty * unitCost
          }
          break
        }
      }
      return result
    })

    watch(allocatedItems, (newItems) => {
      const validSkus = new Set(newItems.map(i => i.item_sku))
      Object.keys(quantityOverrides.value).forEach(sku => {
        if (!validSkus.has(sku)) delete quantityOverrides.value[sku]
      })
    })

    const displayedItems = computed(() =>
      allocatedItems.value.map(item => {
        const overriddenQty = quantityOverrides.value[item.item_sku] ?? item.qty_to_restock
        const qty = Math.max(1, Number(overriddenQty) || 1)
        return { ...item, display_qty: qty, display_subtotal: qty * item.unit_cost }
      })
    )

    const setOverride = (sku, value) => {
      const qty = Math.max(1, parseInt(value, 10) || 1)
      quantityOverrides.value[sku] = qty
    }

    const budgetUsed = computed(() =>
      displayedItems.value.reduce((sum, item) => sum + item.display_subtotal, 0)
    )

    const budgetRemaining = computed(() => budget.value - budgetUsed.value)

    const formatCurrency = (value) =>
      new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(value)

    const placeOrder = async () => {
      submitting.value = true
      orderSuccess.value = false
      try {
        await api.createRestockingOrder({
          items: displayedItems.value.map(item => ({
            sku: item.item_sku,
            name: item.item_name,
            quantity: item.display_qty,
            unit_cost: item.unit_cost
          }))
        })
        orderSuccess.value = true
        budget.value = 50000
      } catch (err) {
        error.value = 'Failed to place order. Please try again.'
      } finally {
        submitting.value = false
      }
    }

    return {
      t,
      budget,
      loading,
      submitting,
      orderSuccess,
      error,
      allocatedItems,
      displayedItems,
      quantityOverrides,
      setOverride,
      budgetUsed,
      budgetRemaining,
      formatCurrency,
      placeOrder
    }
  }
}
</script>

<style scoped>
.restocking-view {
  padding: 0;
}

.page-description {
  color: #64748b;
  margin-top: 0.25rem;
  font-size: 0.9rem;
}

.budget-card {
  margin-bottom: 1.25rem;
}

.budget-controls {
  padding: 1rem 0 0.25rem;
}

.slider-row {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.budget-slider {
  width: 100%;
  accent-color: #2563eb;
}

.budget-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
  min-width: 8rem;
  text-align: right;
}

.budget-summary {
  display: flex;
  flex-direction: row;
  gap: 2rem;
  margin-top: 1rem;
}

.budget-stat {
  display: flex;
  flex-direction: column;
}

.budget-label {
  font-size: 0.8rem;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 600;
}

.budget-amount.used {
  font-size: 1.1rem;
  font-weight: 600;
  color: #dc2626;
}

.budget-amount.remaining {
  font-size: 1.1rem;
  font-weight: 600;
  color: #059669;
}

.sku-cell {
  font-family: monospace;
  color: #64748b;
  font-size: 0.85rem;
}

.text-right {
  text-align: right;
}

.empty-state {
  padding: 2rem;
  text-align: center;
  color: #64748b;
}

.place-order-row {
  padding: 1rem 0 0;
  display: flex;
  justify-content: flex-end;
}

.place-order-btn {
  background: #2563eb;
  color: white;
  border: none;
  padding: 0.75rem 2rem;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s ease;
}

.place-order-btn:hover:not(:disabled) {
  background: #1d4ed8;
}

.place-order-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.success-banner {
  background: #d1fae5;
  border: 1px solid #6ee7b7;
  color: #065f46;
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
}

.qty-cell {
  width: 120px;
}

.qty-input {
  width: 90px;
  padding: 4px 8px;
  border: 1.5px solid #e2e8f0;
  border-radius: 5px;
  font-size: 13px;
  font-family: inherit;
  text-align: right;
  background: transparent;
  color: inherit;
  -moz-appearance: textfield;
  transition: border-color 0.15s;
}
.qty-input::-webkit-inner-spin-button,
.qty-input::-webkit-outer-spin-button {
  opacity: 1;
}
.qty-input:focus {
  outline: none;
  border-color: #2563eb;
}

tr.qty-edited .qty-input {
  border-color: #2563eb;
  background: #eff6ff;
}
</style>
