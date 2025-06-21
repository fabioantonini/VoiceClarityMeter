# VoIP Quality Monitor

## Overview

A real-time VoIP call quality monitoring system built with Python Flask that implements a SIP server, RTP packet processor, and web-based dashboard. The application measures call quality metrics including MOS (Mean Opinion Score), jitter, packet loss, and delay using no-reference quality assessment techniques.

## System Architecture

### Backend Architecture
- **Flask Web Application** - Main application server handling HTTP requests and WebSocket connections
- **SIP Server** - Custom UDP-based SIP server for handling VoIP session management
- **RTP Processor** - Real-time processing of RTP audio packets for quality analysis
- **Call Manager** - Central orchestrator for call state management and data persistence
- **MOS Calculator** - Implementation of E-Model algorithm for quality score calculation

### Frontend Architecture
- **Server-side rendering** with Jinja2 templates
- **Bootstrap 5** for responsive UI components
- **WebSocket** integration using Flask-SocketIO for real-time updates
- **Chart.js** for data visualization (referenced but not implemented)
- **DataTables** for tabular data management

### Communication Flow
- SIP signaling on UDP and TCP port 5060 (dual transport support)
- RTP media processing on dynamically allocated ports
- WebSocket connections for real-time dashboard updates
- RESTful API endpoints for data retrieval

## Key Components

### Core Python Modules

1. **app_simple.py** - Main Flask application with routes and WebSocket handlers
2. **sip_server_tcp.py** - SIP protocol implementation with UDP and TCP transport support
3. **rtp_processor.py** - RTP packet analysis and quality metric calculation
4. **call_manager.py** - Call state management and data persistence
5. **mos_calculator.py** - E-Model based MOS calculation algorithm
6. **config_helper.py** - SIP client configuration assistance

### Web Interface

1. **index.html** - Landing page with feature overview
2. **dashboard.html** - Real-time monitoring interface
3. **config.html** - SIP client configuration helper
4. **JavaScript modules** - Client-side logic for dashboard and configuration

### Quality Metrics

- **MOS Score** - Mean Opinion Score (1.0-5.0) using E-Model
- **Packet Loss Rate** - Percentage of lost RTP packets
- **Jitter** - Variation in packet arrival times
- **Delay** - One-way transmission delay
- **Call Duration** - Active call time tracking

## Data Flow

1. **Call Initiation**: SIP INVITE received → Call Manager creates session → RTP Processor starts
2. **Quality Monitoring**: RTP packets analyzed → Metrics calculated → MOS score computed
3. **Real-time Updates**: Quality data → WebSocket broadcast → Dashboard visualization
4. **Call Termination**: SIP BYE received → Final metrics calculated → Data persisted to JSON

## External Dependencies

### Python Packages
- **Flask** - Web framework and HTTP server
- **Flask-SocketIO** - WebSocket support for real-time communication
- **NumPy** - Mathematical operations for quality calculations

### Frontend Libraries
- **Bootstrap 5** - CSS framework for responsive design
- **Font Awesome** - Icon library
- **DataTables** - Enhanced table functionality
- **Socket.IO** - WebSocket client library

### Network Protocols
- **SIP (Session Initiation Protocol)** - VoIP session management over UDP and TCP
- **RTP (Real-time Transport Protocol)** - Audio packet delivery
- **UDP/TCP** - Dual transport layer support for SIP signaling
- **WebSocket** - Real-time dashboard communication

## Deployment Strategy

### Development Environment
- **Replit** platform with Python 3.11 runtime
- **Flask development server** on port 5000
- **Automatic dependency installation** via pip

### Production Considerations
- SIP server requires UDP port 5060 accessibility
- RTP processing needs dynamic port allocation
- WebSocket support for real-time features
- JSON file-based data persistence (suitable for lightweight deployment)

### Scalability Limitations
- Single-threaded SIP processing
- File-based data storage
- In-memory call state management
- No authentication or multi-tenancy support

## Changelog

- June 21, 2025: Initial setup with UDP SIP server
- June 21, 2025: Added TCP transport support for SIP protocol with dual UDP/TCP operation
- June 21, 2025: Fixed JavaScript WebSocket connection issues and simplified dashboard interface
- June 21, 2025: Converted system to SIP Registrar/Proxy for Asterisk gateway with FXS interfaces
- June 21, 2025: Added gateway status monitoring and registered devices display in dashboard

## User Preferences

Preferred communication style: Simple, everyday language (Italian).
Technical requirements: 
- Support for both UDP and TCP transport protocols for SIP communication
- VoIP gateway integration: Asterisk-based gateway with two FXS interfaces for traditional phones
- System acts as SIP Registrar and Proxy for gateway device registration and call routing