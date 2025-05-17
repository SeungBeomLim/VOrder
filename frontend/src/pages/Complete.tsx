import { useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

export default function Complete() {
  const navigate = useNavigate();
  const location = useLocation();
  const orderData = location.state?.order;

  useEffect(() => {
    if (orderData && Array.isArray(orderData)) {
      const stored = localStorage.getItem('orderHistory');
      const parsed = stored ? JSON.parse(stored) : [];

      const current = orderData[0];

      const newOrder = {
        id: parsed.length + 1,
        items: [current.menu],
        total: parseFloat(current.price).toFixed(2),
        size: current.size || '',
        extra: current.extra || '',
        eta: current.ETA || '',
      };

      const lastOrder = parsed[parsed.length - 1];

      const isDuplicate =
        lastOrder &&
        JSON.stringify({
          items: lastOrder.items,
          total: lastOrder.total,
          size: lastOrder.size,
          extra: lastOrder.extra,
          eta: lastOrder.eta,
        }) ===
        JSON.stringify({
          items: newOrder.items,
          total: newOrder.total,
          size: newOrder.size,
          extra: newOrder.extra,
          eta: newOrder.eta,
        });

      if (!isDuplicate) {
        parsed.push(newOrder);
        localStorage.setItem('orderHistory', JSON.stringify(parsed));
      }
    }

    const timeout = setTimeout(() => {
      navigate('/');
    }, 5000);

    return () => clearTimeout(timeout);
  }, [navigate, orderData]);

  return (
    <div className="w-[390px] h-[844px] mx-auto bg-[#F6F6F6] flex flex-col items-center justify-start pt-10 px-6 shadow-lg rounded-xl overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between w-full">
        <div className="w-10 h-10 rounded-full bg-white shadow flex items-center justify-center">
          <img src="/menu.svg" alt="Menu" className="w-5 h-5 z-10" />
        </div>
        <h1 className="text-xl font-bold text-[#1C1B1F]">VOrder</h1>
        <div className="w-10 h-10 rounded-full bg-white shadow flex items-center justify-center">
          <img src="/notification.svg" alt="Notification" className="w-5 h-5 z-10" />
        </div>
      </div>

      {/* Checkmark Icon */}
      <div className="mt-32 w-28 h-28 rounded-full bg-[#00704A] flex items-center justify-center shadow-lg">
        <img src="/checkmark.svg" alt="Checkmark" className="w-10 h-10" />
      </div>

      {/* Confirmation Text */}
      <p className="mt-10 text-2xl font-semibold text-[#1C1B1F]">Order Completed</p>
      <p className="text-sm text-[#5F5F5F] mt-2">You will be redirected to Home shortly.</p>

      {/* Button (optional) */}
      <button
        onClick={() => navigate('/')}
        className="mt-10 bg-[#00704A] text-white px-6 py-3 rounded-full text-sm shadow-md"
      >
        Back to Home
      </button>
    </div>
  );
}
