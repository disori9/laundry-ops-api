# 🧺 Laundry Hub: POS & Management System

A full-stack Point of Sale (POS) and Operations Management system designed specifically for modern laundromats. This application handles the complete customer lifecycle: from order intake and dynamic load estimation, to shop floor workflow tracking, and finally, executive business analytics.

## 🚀 Live Features

### 1. Smart Drop-off System (`order.html`)
* **Indestructible Weight Parser:** Translates both decimal (e.g., 5.5) and fractional (e.g., 5 1/2) inputs into exact backend weight logic.
* **Dynamic Load Estimator:** Automatically calculates the required number of machine loads and dynamically generates a visual progress bar of machine fullness.
* **Quick-Add CRM:** Register walk-in customers seamlessly via a modal without interrupting the active order flow.

### 2. Live Shop Floor (`index.html`)
* **Workflow Kanban:** Track baskets through discrete statuses: `Wait: Wash` -> `Washing` -> `Drying` -> `Folding` -> `Bagged`.
* **QA Verification Modal:** Forces staff to verify exact item counts before an order can be bagged, preventing missing item disputes.
* **Hardware Collision Prevention:** Backend and frontend error handling that prevents assigning baskets to occupied machines.

### 3. Customer CRM (`customer.html`)
* **Live Search:** Instantaneous filtering of the customer database by name or mobile number.
* **Staff-Safe Privacy:** Displays operational data (Visits, Unpaid Orders) to staff while hiding sensitive lifetime financial data from the shop floor.
* **Order Audit Trail:** Clickable profiles reveal a chronological history of every order and its payment status.

### 4. Executive Dashboard (`owner.html`)
* **Role-Based Access Control:** Frontend PIN-gate prevents unauthorized access to business intelligence.
* **Bento Box UI:** Modern CSS-Grid layout optimized for both wide desktop monitors and mobile views.
* **Data Visualization:** Integrates Chart.js to visualize 7-Day and 6-Month revenue trends dynamically.
* **Business Intelligence Engine:** Automatically calculates Average Ticket Size, Peak Operating Hours, and a "Top 5 VIP" customer leaderboard.

## 💻 Tech Stack
* **Frontend:** HTML5, CSS3 (Custom Variables, CSS Grid/Flexbox), Vanilla JavaScript (ES6+).
* **Data Visualization:** Chart.js
* **Backend:** Python REST API
* **Design Pattern:** Asynchronous Promise fetching with In-Memory UI rendering.

## ⚙️ Local Setup & Installation

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/yourusername/laundry-hub.git](https://github.com/disori9/laundry-hub.git)
   ```

2. **Start the Backend:**
   Ensure your Python server is running and listening on port 8000.
   ```bash
   # Example command depending on your Python framework
   uvicorn main:app --reload --port 8000
   ```

3. **Run the Frontend:**
   Launch the application using a local development server (like VS Code Live Server). Do not open the HTML files directly from the file explorer, as the Fetch API requires a web server to make cross-origin requests.

4. **Access:**
   Navigate to your local server port (e.g., `http://127.0.0.1:5500/index.html`).
   *Note: Default Owner Dashboard PIN is `8888`.*

---
*Developed by Serefel*