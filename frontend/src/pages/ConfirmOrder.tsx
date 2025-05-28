import { useEffect, useRef, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

export default function ConfirmOrder() {
  const navigate = useNavigate();
  const [orderData, setOrderData] = useState<any[]>([]);
  const ttsPlayedRef = useRef(false);

  useEffect(() => {
    const loadDataAndPlayTTS = async () => {
      try {
        const res = await fetch('http://localhost:8000/media/final_order.json');
        const data = await res.json();

        const orderItem = {
          customer: data.customer,
          number: data.number,
          menu: data.menu,
          size: data.size,
          extra: data.extra,
          price: data.price,
          ETA: data.ETA,
        };

        setOrderData([orderItem]);

        // ✅ TTS는 단 한 번만 실행되도록 보장
        if (!ttsPlayedRef.current) {
          const ttsText = `You ordered a ${data.size} ${data.menu} ${data.extra ? 'with ' + data.extra : ''}. The total is ${data.price}₩.`;
          const audio = new Audio(`http://localhost:8000/api/confirm-tts?text=${encodeURIComponent(ttsText)}`);
          console.log('📢 TTS audio.play() triggered');
          audio.play();
          ttsPlayedRef.current = true;
        }
      } catch (err) {
        console.error('❌ Failed to load order summary or play TTS:', err);
      }
    };

    loadDataAndPlayTTS();
  }, []);

  const handleCancel = () => {
    navigate('/');
  };

  const handleNext = () => {
    navigate('/complete', { state: { order: orderData } });
  };

  const subtotal = orderData.reduce((sum, item) => sum + item.price, 0);
  const tax = 0.08 * subtotal;
  const discount = 1.0;
  const total = (subtotal + tax - discount).toFixed(2);

  return (
    <div className="w-[390px] h-[844px] mx-auto bg-[#F6F6F6] items-center justify-start pt-6 px-2 flex flex-col shadow-lg rounded-xl overflow-hidden relative">
      <div className="w-full flex items-center justify-between p-4">
        <div className="w-10 h-10 rounded-full bg-white shadow flex items-center justify-center">
          <img src="/menu.svg" alt="Menu" className="w-5 h-5 z-10" />
        </div>
        <h1 className="text-xl font-bold text-[#1C1B1F]">VOrder</h1>
        <div className="w-10 h-10 rounded-full bg-white shadow flex items-center justify-center">
          <img src="/notification.svg" alt="Notification" className="w-5 h-5 z-10" />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-6 pt-4 pb-40 w-full">
        <h2 className="text-sm text-black font-semibold mb-4">Order Summary</h2>

        {orderData.map((item, idx) => (
          <div key={idx} className="mb-4 border rounded-lg p-4 bg-white shadow-sm">
            <p className="font-semibold text-black">{item.menu}</p>
            <div className="flex justify-between mt-1 text-sm text-[#5F5F5F]">
              <p>Size: {item.size || 'Regular'} {item.extra ? `· Extra: ${item.extra}` : ''}</p>
              <p>{item.price.toFixed(2)}₩</p>
            </div>
          </div>
        ))}
      </div>

      <div className="absolute bottom-0 left-0 w-full bg-[#F6F6F6] px-6 py-4 border-t shadow-lg">
        <div className="border rounded-lg p-4 mb-4 bg-white">
          <p className="text-sm text-black">Subtotal: {subtotal.toFixed(2)}₩</p>
          <p className="text-sm text-black">Tax: {tax.toFixed(2)}₩</p>
          <p className="text-sm text-black">Discount: -{discount.toFixed(2)}₩</p>
          <hr className="my-2" />
          <p className="text-base font-semibold text-black">Total: {total}₩</p>
        </div>

        <div className="flex justify-between">
          <button
            onClick={handleCancel}
            className="bg-[#A3A3A3] text-white px-8 py-3 rounded-lg text-sm"
          >
            Cancel
          </button>
          <button
            onClick={handleNext}
            className="bg-[#00704A] text-white px-8 py-3 rounded-lg text-sm"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
