/**
 * ULTRA v3.0 - WebSocket Manager
 * ===============================
 * 
 * WebSocket connection manager for real-time Slow Path updates.
 * Implements F-2.4 specification with automatic reconnection.
 */

import type { WebSocketMessage } from '../types';

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/api/v1/ws';

export class WebSocketManager {
  private ws: WebSocket | null = null;
  private sessionId: string | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 2000; // 2 seconds
  private onMessageCallback: ((message: WebSocketMessage) => void) | null = null;
  
  /**
   * Connect to WebSocket for a specific session
   */
  connect(sessionId: string, onMessage: (message: WebSocketMessage) => void) {
    this.sessionId = sessionId;
    this.onMessageCallback = onMessage;
    
    try {
      this.ws = new WebSocket(`${WS_URL}/sessions/${sessionId}`);
      
      this.ws.onopen = () => {
        console.log(`🔌 WebSocket connected: ${sessionId}`);
        this.reconnectAttempts = 0;
      };
      
      this.ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          this.onMessageCallback?.(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };
      
      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
      
      this.ws.onclose = (event) => {
        console.log(`🔌 WebSocket closed: ${event.code} ${event.reason}`);
        
        // Attempt reconnection if not intentionally closed
        if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++;
          console.log(`Reconnecting... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
          
          setTimeout(() => {
            if (this.sessionId && this.onMessageCallback) {
              this.connect(this.sessionId, this.onMessageCallback);
            }
          }, this.reconnectDelay * this.reconnectAttempts);
        }
      };
      
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
    }
  }
  
  /**
   * Close WebSocket connection
   */
  disconnect() {
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
      this.sessionId = null;
      this.onMessageCallback = null;
    }
  }
  
  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

// Export singleton instance
export const wsManager = new WebSocketManager();
