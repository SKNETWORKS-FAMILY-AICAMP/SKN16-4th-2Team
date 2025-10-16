import { useState, useRef } from 'react';
import { UserCircleIcon } from '@heroicons/react/24/outline';
import { useAuthStore } from '../store/authStore';

export default function MyPage() {
  const { user, updateUser } = useAuthStore();
  const [photoUrl, setPhotoUrl] = useState(user?.photo_url || '');
  const [uploading, setUploading] = useState(false);
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
    </div>
  );
}
