import { createSlice } from '@reduxjs/toolkit'

const chatSlice = createSlice({
  name: 'chat',
  initialState: {
    messages: [],
    isLoading: false,
  },
  reducers: {
    addMessage(state, action) {
      state.messages.push(action.payload)
    },
    setLoading(state, action) {
      state.isLoading = action.payload
    },
    clearMessages(state) {
      state.messages = []
    },
  },
})

export const { addMessage, setLoading, clearMessages } = chatSlice.actions

export default chatSlice.reducer