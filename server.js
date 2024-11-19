const fs = require("fs");
const express = require("express");
const path = require("path");
const app = express();

app.use(express.json());

// Serve static files from the Crypto directory
app.use(express.static(path.join(__dirname)));

const dbPath = "./database.json";

// Get clients
app.get("/clients", (req, res) => {
  const data = fs.readFileSync(dbPath);
  res.json(JSON.parse(data));
});

// Save clients
app.post("/clients", (req, res) => {
  console.log("Received clients data:", req.body); // Log the received data
  const clients = req.body;
  fs.writeFileSync(dbPath, JSON.stringify(clients, null, 2));
  res.json({ message: "Clients updated successfully!" });
});

app.listen(3100, () => console.log("Server running on http://localhost:3100"));