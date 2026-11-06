import { createSlice } from '@reduxjs/toolkit'

const initialState = {
  summary: {
    deviation_id: null,
    title: null,
    product_name: null,
    batch_number: null,
    process_step: null,
    equipment_id: null,
    date_detected: null,
    reported_by: null,
    problem_statement: null,
    affected_quantity: null,
    immediate_containment: null,
  },
  risk: {
    severity: null,
    batch_impact: null,
    recommended_next_action: null,
    regulatory_reportability: null,
    rationale: null,
  },
  analysis: {
    whys: [],
    causes: [],
    evidence: [],
    capas: [],
  },
  highlighted: [],
}

const formSlice = createSlice({
  name: 'form',
  initialState,
  reducers: {
    setForm(state, action) {
      state.summary = action.payload.summary
      state.risk = action.payload.risk
      state.analysis = action.payload.analysis
    },
    setHighlighted(state, action) {
      state.highlighted = action.payload
    },
    clearHighlighted(state) {
      state.highlighted = []
    },
    resetForm() {
      return initialState
    },
  },
})

export const { setForm, setHighlighted, clearHighlighted, resetForm } =
  formSlice.actions

export default formSlice.reducer