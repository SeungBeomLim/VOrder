import { useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';

export default function Orders() {
  const navigate = useNavigate();
  const [orders, setOrders] = useState<any[]>([]);

  useEffect(() => {
    const stored = localStorage.getItem('orderHistory');
    const parsed = stored ? JSON.parse(stored) : [];
    const withIds = parsed.map((order: any, idx: number) => ({ id: idx + 1, ...order }));
    const sorted = withIds.sort((a, b) => b.id - a.id);
    setOrders(sorted);
  }, []);

  const handleOrderClick = (orderId: number) => {
    navigate(`/order-detail/${orderId}`);
  };

  const handleClearOrders = () => {
    localStorage.removeItem('orderHistory');
    setOrders([]);
  };

  return (
    <div className="w-[390px] h-[844px] mx-auto bg-[#F6F6F6] flex flex-col shadow-lg rounded-xl overflow-hidden relative">
      {/* Fixed Header */}
      <div className="absolute top-0 left-0 w-full bg-[#F6F6F6] z-10 flex items-center justify-between p-4 h-[60px]">
        <img src="/menu.svg" alt="Menu" className="w-5 h-5" />
        <h1 className="text-lg font-bold text-[#1C1B1F]">VOrder</h1>
        <img src="/notification.svg" alt="Notification" className="w-5 h-5" />
      </div>

      {/* Scrollable Content */}
      <div className="pt-[70px] pb-[140px] overflow-y-auto flex-1 px-4">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-sm font-semibold text-black">Incoming Orders</h2>
          <button
            onClick={handleClearOrders}
            className="text-sm text-red-500 underline hover:text-red-700"
          >
            Clear All
          </button>
        </div>

        {orders.length === 0 && (
          <p className="text-sm text-gray-500">No orders yet.</p>
        )}

        {orders.map((order) => (
          <div
            key={order.id}
            onClick={() => handleOrderClick(order.id)}
            className="bg-white rounded-xl p-4 mb-4 shadow-sm cursor-pointer hover:bg-[#f0f0f0] transition"
          >
            <div className="flex justify-between mb-2">
              <p className="font-semibold text-[#1C1B1F]">Order {order.id}</p>
              <p className="font-semibold text-[#1C1B1F]">
                {order.total && !isNaN(parseFloat(order.total)) ? `${parseFloat(order.total).toFixed(2)}$` : 'N/A'}
              </p>
            </div>
            <div className="text-sm text-[#5F5F5F]">
              {(order.items || []).map((item: string, index: number) => (
                <p key={index}>{item}</p>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Fixed Footer */}
      <div className="absolute bottom-0 left-0 w-full bg-[#F6F6F6] px-6 py-4 border-t flex justify-between items-center z-10">
        <button
          onClick={() => navigate('/')}
          className="bg-[#9B9B9B] text-white rounded-full px-8 py-3 text-sm font-medium shadow"
        >
          Cancel
        </button>
        <button
          onClick={() => {}}
          className="bg-[#00704A] text-white rounded-full px-8 py-3 text-sm font-medium shadow"
        >
          Next
        </button>
      </div>
    </div>
  );
}
