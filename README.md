# enterprise_software

## Project Overview

As the client (a mid-sized manufacturing firm with 500+ employees across multiple sites), I'm excited to partner on building two critical enterprise applications to streamline our operations. These tools will replace outdated legacy systems, enabling scalable growth to handle 10,000+ users/transactions daily while ensuring 99.9% uptime, data security (GDPR/CCPA compliant), and mobile responsiveness.

We will be building a Project Management System (PMS) and Inventory Management System (IMS) using Django Rest Framework for the PMS and Golang for the IMS.

## About the Projects

### Project Management System (PMS)

Our PMS is a web-based application that allows teams to manage projects, tasks, and teams in real-time. It will be customized for our enterprise needs, focusing on cross-departmental workflows, resource allocation, and analytics. The PMS will be built with Django for rapid development and robust backend handling, it will support integrations with email (e.g., Outlook), calendars (e.g., Google Workspace), and our IMS for inventory-linked projects (e.g., procurement tasks).

### Inventory Management System (IMS)

Our IMS is a web-based application that allows teams to track stock levels, orders, and supply chain logistics. It will be modeled after modern ERP modules (e.g., SAP Inventory), it emphasizes real-time updates, predictive reordering, and supplier portals. The IMS will be built with Golang for concurrency and low-latency processing, it will integrate with PMS for project-based inventory pulls and external APIs (e.g., shipping providers like FedEx).

## Key Requirements

### Non-Functional Requirements (Applies to Both)

- **Scalability**: Horizontal scaling; handle spikes (e.g., end-of-quarter rushes) with auto-scaling.
- **Reliability**: Redundancy (e.g., DB replicas), backups (daily), and disaster recovery (RTO <4 hours).
- **Security**: OAuth2/JWT auth, encryption at rest/transit, audit logs, vulnerability scans.
- **Performance**: <200ms API response; offline support via PWA.