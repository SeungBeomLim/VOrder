import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import Orders from './pages/Orders';
import OrderDetail from './pages/OrderDetail';
import Order from './pages/Order';
import ConfirmOrder from './pages/ConfirmOrder';
import Complete from './pages/Complete';

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/orders" element={<Orders />} />
        <Route path="/order-detail/:id" element={<OrderDetail />} />
        <Route path="/order" element={<Order />} />
        <Route path="/confirm-order" element={<ConfirmOrder />} />
        <Route path="/complete" element={<Complete />} />
      </Routes>
    </Router>
  );
}
