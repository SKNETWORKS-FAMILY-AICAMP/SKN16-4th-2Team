import { useState, useRef } from 'react';
import { UserCircleIcon, QrCodeIcon } from '@heroicons/react/24/outline';
import { useAuthStore } from '../store/authStore';
import { authAPI } from '../utils/api';
import { QRCodeSVG } from 'qrcode.react';

export default function MyPage() {
  const { user, updateUser } = useAuthStore();
  const [photoUrl, setPhotoUrl] = useState(user?.photo_url || '');
  const [uploading, setUploading] = useState(false);
  const [showQR, setShowQR] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!user) return <div>로그인이 필요합니다.</div>;

  // 이미지 업로드 핸들러
  const handleImageChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      // 실제 업로드 API가 있다면 여기에 구현
      // 예시: 서버에 업로드 후 URL 반환
      // const url = await uploadProfileImage(file);
      // setPhotoUrl(url);
      // updateUser({ ...user, photo_url: url });
      // 데모용: 로컬 미리보기
      const reader = new FileReader();
      reader.onload = (ev) => {
        if (ev.target?.result) {
          setPhotoUrl(ev.target.result as string);
          updateUser({ ...user, photo_url: ev.target.result as string });
        }
      };
      reader.readAsDataURL(file);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="max-w-lg mx-auto bg-white p-10 rounded-xl shadow flex flex-col items-center mt-14">
      <h2 className="text-2xl font-bold mb-8 self-start">내 정보</h2>
      {/* 프로필 사진, 이름, 역할 */}
      <div className="flex flex-col items-center mb-8">
        <div className="relative w-28 h-28 mb-3">
          {photoUrl ? (
            <img src={photoUrl} alt={user.name} className="w-28 h-28 rounded-full object-cover border" />
          ) : (
            <UserCircleIcon className="w-28 h-28 text-gray-300" />
          )}
          <button
            className="absolute bottom-2 right-2 bg-blue-500 text-white rounded-full p-1 shadow hover:bg-blue-600 focus:outline-none"
            onClick={() => fileInputRef.current?.click()}
            title="프로필 이미지 업로드"
            type="button"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M15.232 5.232l3.536 3.536M9 13l6-6m2 2a2.828 2.828 0 11-4-4 2.828 2.828 0 014 4z" /></svg>
          </button>
          <input
            type="file"
            accept="image/*"
            ref={fileInputRef}
            className="hidden"
            onChange={handleImageChange}
            disabled={uploading}
          />
        </div>
        <div className="text-xl font-bold mt-1 text-center">{user.name}</div>
        <div className="text-blue-500 text-sm font-medium text-center">mentee</div>
      </div>

      {/* 정보 항목 */}
      <div className="w-full flex flex-col gap-5">
        <div className="flex flex-row justify-between items-center">
          <span className="text-gray-500 font-medium">사원번호</span>
          <span className="text-lg font-semibold text-gray-800">{user.employee_number || '-'}</span>
        </div>
        <div className="flex flex-row justify-between items-center">
          <span className="text-gray-500 font-medium">부서/팀</span>
          <span className="text-lg font-semibold text-gray-800">
            {user.team && user.team_number
              ? `${user.team} ${user.team_number}`
              : user.team || user.team_number || '-'}
          </span>
        </div>
        <div className="flex flex-row justify-between items-center">
          <span className="text-gray-500 font-medium">관심사</span>
          <span className="text-lg font-semibold text-gray-800">
            {user.interests
              ? (Array.isArray(user.interests)
                  ? user.interests.join(', ')
                  : String(user.interests).replace(/\[|\]|"/g, '').split(',').map(s => s.trim()).join(', '))
              : '-'}
          </span>
        </div>
      </div>

      {/* QR 코드 섹션 */}
      <div className="w-full mt-8 pt-8 border-t border-gray-200">
        <button
          onClick={() => setShowQR(!showQR)}
          className="w-full flex items-center justify-center gap-2 py-3 bg-primary-600 text-white rounded-lg font-semibold hover:bg-primary-700 transition-colors"
        >
          <QrCodeIcon className="w-5 h-5" />
          {showQR ? '사원증 QR 코드 숨기기' : '내 사원증 QR 코드 보기'}
        </button>

        {showQR && (
          <div className="mt-6">
            {/* 사원증 카드 스타일 */}
            <div className="relative bg-gradient-to-br from-blue-900 via-blue-800 to-blue-900 rounded-2xl shadow-2xl overflow-hidden">
              {/* 배경 패턴 */}
              <div className="absolute inset-0 opacity-10">
                <div className="absolute top-0 left-0 w-32 h-32 bg-white rounded-full -translate-x-16 -translate-y-16"></div>
                <div className="absolute bottom-0 right-0 w-40 h-40 bg-white rounded-full translate-x-20 translate-y-20"></div>
              </div>
              
              {/* 카드 내용 */}
              <div className="relative p-8">
                {/* 헤더 */}
                <div className="text-center mb-6">
                  <div className="inline-flex items-center justify-center w-12 h-12 bg-white/20 backdrop-blur-sm rounded-full mb-3">
                    <svg className="w-7 h-7 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M10.394 2.08a1 1 0 00-.788 0l-7 3a1 1 0 000 1.84L5.25 8.051a.999.999 0 01.356-.257l4-1.714a1 1 0 11.788 1.838L7.667 9.088l1.94.831a1 1 0 00.787 0l7-3a1 1 0 000-1.838l-7-3zM3.31 9.397L5 10.12v4.102a8.969 8.969 0 00-1.05-.174 1 1 0 01-.89-.89 11.115 11.115 0 01.25-3.762zM9.3 16.573A9.026 9.026 0 007 14.935v-3.957l1.818.78a3 3 0 002.364 0l5.508-2.361a11.026 11.026 0 01.25 3.762 1 1 0 01-.89.89 8.968 8.968 0 00-5.35 2.524 1 1 0 01-1.4 0zM6 18a1 1 0 001-1v-2.065a8.935 8.935 0 00-2-.712V17a1 1 0 001 1z"/>
                    </svg>
                  </div>
                  <h3 className="text-xl font-bold text-white mb-1">디지털 사원증</h3>
                  <p className="text-blue-200 text-sm">Digital Employee ID</p>
                </div>

                {/* QR 코드 */}
                <div className="flex justify-center mb-6">
                  <div className="bg-white p-6 rounded-2xl shadow-lg">
                    <QRCodeSVG 
                      value={`qr-login:${user.email}`}
                      size={180}
                      level="H"
                      includeMargin={false}
                    />
                  </div>
                </div>

                {/* 사용자 정보 */}
                <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4 mb-4">
                  <div className="flex items-center justify-between text-white">
                    <div className="text-left">
                      <p className="text-xs text-blue-200 mb-1">이름 / Name</p>
                      <p className="font-semibold text-lg">{user.name}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-xs text-blue-200 mb-1">사원번호 / ID</p>
                      <p className="font-mono font-semibold">{user.employee_number}</p>
                    </div>
                  </div>
                </div>

                {/* 안내 메시지 */}
                <div className="text-center">
                  <p className="text-blue-100 text-sm mb-2">
                    로그인 시 이 QR 코드를 스캔하세요
                  </p>
                  <div className="inline-flex items-center gap-2 px-4 py-2 bg-green-500/20 border border-green-400/30 rounded-full">
                    <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                    <p className="text-xs text-green-100 font-medium">유효한 사원증</p>
                  </div>
                </div>
              </div>

              {/* 하단 장식 바 */}
              <div className="h-2 bg-gradient-to-r from-blue-400 via-blue-300 to-blue-400"></div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
