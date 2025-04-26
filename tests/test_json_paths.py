<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Ledger Freshness Visual Options Demo</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    body { background-color: #eef2f5; }
    .ledger-box {
      width: 220px;
      height: 110px;
      border-radius: 12px;
      padding: 0.5rem;
      margin: 0.5rem;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      font-weight: bold;
      background: white;
      transition: background 0.5s, box-shadow 0.5s;
      box-shadow: 0 0 5px rgba(0,0,0,0.1);
    }
    .icon {
      font-size: 2rem;
    }
    .fresh-gradient { background: linear-gradient(90deg, #d4edda, #c3e6cb); }
    .warning-gradient { background: linear-gradient(90deg, #fff3cd, #ffeeba); }
    .stale-gradient { background: linear-gradient(90deg, #f8d7da, #f5c6cb); }
  </style>
</head>

<body>

<div class="container text-center mt-5">

  <h2>Ledger Freshness Demo - New Styles</h2>

  <div class="d-flex flex-wrap justify-content-center">

    <!-- Option 1 -->
    <div class="ledger-box fresh-gradient">
      <div class="icon">💵</div>
      <small>Last: 9:30 AM</small>
      <small>Next in: 2m 30s</small>
    </div>

    <!-- Option 2 -->
    <div class="ledger-box warning-gradient">
      <div class="icon">📊</div>
      <small>Last: 9:25 AM</small>
      <small>Next in: 1m 10s</small>
    </div>

    <!-- Option 3 -->
    <div class="ledger-box stale-gradient">
      <div class="icon">🌪️</div>
      <small>Last: 8:55 AM</small>
      <small>Next in: 0m 20s</small>
    </div>

    <!-- Option 4 -->
    <div class="ledger-box fresh-gradient">
      <div class="icon">💵</div>
      <small>Last: 9:30 AM</small>
      <small>Next in: 5m 00s</small>
    </div>

  </div>

</div>

</body>
</html>
