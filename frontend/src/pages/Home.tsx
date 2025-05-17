import { useNavigate } from 'react-router-dom';

export default function Home() {
  const navigate = useNavigate();

  const handleMicClick = () => {
    navigate('/order');
  };

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

      {/* Mic button */}
      <div
        onClick={handleMicClick}
        className="mt-16 w-64 h-64 rounded-full bg-gradient-to-b from-[#367145] to-[#004B28] flex items-center justify-center shadow-lg relative cursor-pointer"
      >
        <div className="absolute inset-0 rounded-full border-[6px] border-[#D4E8DD]" />
        <img src="/mic.svg" alt="Mic" className="w-10 h-10 z-10" />
      </div>

      {/* Prompt text */}
      <p className="mt-10 text-[#5F5F5F] text-base">Say something to order</p>

      {/* Deals Section */}
      <div className="w-full mt-10">
        <h2 className="text-sm text-black font-semibold mb-2">Deals</h2>
        <div className="bg-[#F7F7F8] rounded-xl p-4 shadow text-center text-[#333333]">
          <p className="text-sm">
            Say “I’d like a Cherry Blossom Latte”<br />→ Get a free extra shot today!
          </p>
        </div>
      </div>

      {/* Favorites Section */}
      <div className="w-full mt-8">
        <h2 className="text-sm text-[#5F5F5F] mb-2">Favorites</h2>
        <div className="grid grid-cols-3 gap-3">
          <div className="flex flex-col items-center justify-center bg-white rounded-2xl py-4 shadow">
            <img src="/home.svg" alt="Home" className="w-6 h-6 mb-2" />
            <p className="text-xs text-black">Home</p>
          </div>
          <div
            className="flex flex-col items-center justify-center bg-white rounded-2xl py-4 shadow cursor-pointer"
            onClick={() => navigate('/orders')}
          >
            <img src="/orders.svg" alt="Orders" className="w-6 h-6 mb-2" />
            <p className="text-xs text-black">Orders</p>
          </div>
          <div className="flex flex-col items-center justify-center bg-white rounded-2xl py-4 shadow">
            <img src="/history.svg" alt="Order History" className="w-6 h-6 mb-2" />
            <p className="text-xs text-black">Order History</p>
          </div>
        </div>
      </div>
    </div>
  );
}
