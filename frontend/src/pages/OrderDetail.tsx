import { useParams, useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';

export default function OrderDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [order, setOrder] = useState<any>(null);

  useEffect(() => {
    const storedOrders = localStorage.getItem('orderHistory');
    if (storedOrders && id) {
      const parsed = JSON.parse(storedOrders);
      const index = parseInt(id, 10) - 1;
      if (parsed[index]) setOrder(parsed[index]);
    }
  }, [id]);

  return (
    <div className="w-[390px] h-[844px] mx-auto bg-[#F6F6F6] flex flex-col shadow-lg rounded-xl overflow-hidden relative">
      {/* Fixed Header */}
      <div className="absolute top-0 left-0 w-full bg-[#F6F6F6] z-10 flex items-center justify-between p-4 h-[60px]">
        <img src="/menu.svg" alt="Menu" className="w-5 h-5" />
        <h1 className="text-lg font-bold text-[#1C1B1F]">VOrder</h1>
        <img src="/notification.svg" alt="Notification" className="w-5 h-5" />
      </div>

      <div className="pt-[70px] pb-[140px] overflow-y-auto flex-1 px-4">
        <h2 className="text-lg font-semibold text-black mb-4">Order {id}</h2>
        {order ? (
          <div className="bg-white rounded-xl p-4 shadow-sm mb-4">
            <p className="text-sm text-[#1C1B1F] font-semibold">{order.items.join(', ')}</p>
            <p className="text-sm text-[#5F5F5F]">
              Size: {order.size || 'Regular'} {order.extra ? `· Extra: ${order.extra}` : ''}
            </p>
            <p className="text-sm text-[#1C1B1F] text-right">{order.total}$</p>
            <p className="text-sm text-[#5F5F5F] text-right">ETA: {order.eta}</p>
          </div>
        ) : (
          <p className="text-center text-sm text-[#5F5F5F]">Order not found.</p>
        )}
      </div>

      {/* Fixed Footer */}
      <div className="absolute bottom-0 left-0 w-full bg-[#F6F6F6] px-6 py-4 border-t flex justify-center items-center z-10">
        <button
          onClick={() => navigate('/orders')}
          className="bg-[#00704A] text-white rounded-full px-8 py-3 text-sm font-medium shadow"
        >
          Back to Orders
        </button>
      </div>
    </div>
  );
}
