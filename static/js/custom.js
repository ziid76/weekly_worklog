        $(document).ready(function() {
            // 사이드바 활성 메뉴 표시
            $('.sidebar .nav-link').each(function() {
                if ($(this).attr('href') === window.location.pathname) {
                    $(this).addClass('active');
                }
            });

            // 모바일 사이드바 토글
            $('#sidebarToggle').on('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                console.log('Hamburger button clicked'); // 디버깅용
                toggleSidebar();
            });
            
            // 터치 이벤트 별도 처리 (중복 방지)
            $('#sidebarToggle').on('touchstart', function(e) {
                e.preventDefault();
            });
            
            // 사이드바 오버레이 클릭/터치 시 사이드바 닫기
            $('#sidebarOverlay').on('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                console.log('Overlay clicked'); // 디버깅용
                closeSidebar();
            });
            
            // 사이드바 내부 클릭 시 이벤트 전파 방지
            $('#sidebar').on('click', function(e) {
                e.stopPropagation();
            });
            
            // 사이드바 토글 함수
            function toggleSidebar() {
                const $sidebar = $('#sidebar');
                const $overlay = $('#sidebarOverlay');
                const $body = $('body');
                const $toggleBtn = $('#sidebarToggle');
                
                const isCurrentlyOpen = $sidebar.hasClass('show');
                
                if (isCurrentlyOpen) {
                    closeSidebar();
                } else {
                    openSidebar();
                }
            }
            
            // 사이드바 열기 함수
            function openSidebar() {
                const $sidebar = $('#sidebar');
                const $overlay = $('#sidebarOverlay');
                const $body = $('body');
                const $toggleBtn = $('#sidebarToggle');
                
                // 현재 스크롤 위치 저장
                const scrollTop = $(window).scrollTop();
                $body.data('scroll-position', scrollTop);
                
                $sidebar.addClass('show');
                $overlay.addClass('show');
                $body.addClass('sidebar-open');
                $body.css('top', -scrollTop + 'px');
                
                // 햄버거 버튼 상태 업데이트
                $toggleBtn.addClass('active');
                $toggleBtn.attr('aria-expanded', 'true');
                $toggleBtn.attr('aria-label', '메뉴 닫기');
                
                // 사이드바에 포커스 설정 (접근성)
                setTimeout(() => {
                    $sidebar.find('.nav-link').first().focus();
                }, 300);
            }
            
            // 사이드바 닫기 함수
            function closeSidebar() {
                const $sidebar = $('#sidebar');
                const $overlay = $('#sidebarOverlay');
                const $body = $('body');
                const $toggleBtn = $('#sidebarToggle');
                
                $sidebar.removeClass('show');
                $overlay.removeClass('show');
                $body.removeClass('sidebar-open');
                
                // 스크롤 위치 복원
                const scrollTop = $body.data('scroll-position') || 0;
                $body.css('top', '');
                $(window).scrollTop(scrollTop);
                
                // 햄버거 버튼 상태 초기화
                $toggleBtn.removeClass('active');
                $toggleBtn.attr('aria-expanded', 'false');
                $toggleBtn.attr('aria-label', '메뉴 열기');
            }
            
            // ESC 키로 사이드바 닫기
            $(document).keyup(function(e) {
                if (e.keyCode === 27) { // ESC key
                    closeSidebar();
                }
            });
            
            // 윈도우 리사이즈 시 모바일 사이드바 상태 초기화
            $(window).resize(function() {
                if ($(window).width() >= 768) {
                    closeSidebar();
                }
            });
            
            // 사이드바 메뉴 링크 클릭 처리
            $('.sidebar .nav-link').on('click', function(e) {
                console.log('Menu link clicked:', $(this).attr('href')); // 디버깅용
                
                // 링크가 유효한 경우에만 사이드바 닫기
                const href = $(this).attr('href');
                if (href && href !== '#' && href !== 'javascript:void(0)') {
                    if ($(window).width() < 768) {
                        setTimeout(function() {
                            closeSidebar();
                        }, 100); // 페이지 이동 전 잠시 대기
                    }
                }
            });
            
            // 디버깅 함수들 (개발 중에만 사용)
            window.debugSidebar = function() {
                console.log('Sidebar state:', {
                    sidebarHasShow: $('#sidebar').hasClass('show'),
                    overlayHasShow: $('#sidebarOverlay').hasClass('show'),
                    bodyHasSidebarOpen: $('body').hasClass('sidebar-open'),
                    windowWidth: $(window).width(),
                    sidebarExists: $('#sidebar').length > 0,
                    overlayExists: $('#sidebarOverlay').length > 0,
                    toggleBtnExists: $('#sidebarToggle').length > 0
                });
            };
            
            window.testSidebar = function() {
                console.log('Testing sidebar...');
                toggleSidebar();
            };
            
            // 터치 디바이스 감지
            const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
            if (isTouchDevice) {
                $('body').addClass('touch-device');
                console.log('Touch device detected');
            }
            
            // 페이지 로드 완료 후 초기화
            $(window).on('load', function() {
                console.log('Page loaded, initializing mobile menu...');
                
                // 모바일 환경에서 초기 상태 확인
                if ($(window).width() < 768) {
                    console.log('Mobile view detected');
                    $('#sidebar').removeClass('show');
                    $('#sidebarOverlay').removeClass('show');
                    $('body').removeClass('sidebar-open');
                }
            });

        // 전역 함수들
        function showNotification(message, type = 'info') {
            var alertClass = 'alert-' + type;
            var iconClass = type === 'success' ? 'check-circle' : 
                           type === 'error' ? 'exclamation-triangle' : 
                           type === 'warning' ? 'exclamation-circle' : 'info-circle';
            
            var alertHtml = `
                <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
                    <i class="fas fa-${iconClass} me-2"></i>
                    ${message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            `;
            
            $('.main-content').prepend(alertHtml);
            
            setTimeout(function() {
                $('.alert').first().fadeOut('slow');
            }, 5000);
        }

        function confirmDelete(message = '정말로 삭제하시겠습니까?') {
            return confirm(message);
        }

        // 반응형 테이블
        function makeTableResponsive() {
            $('.table').each(function() {
                if (!$(this).parent().hasClass('table-responsive')) {
                    $(this).wrap('<div class="table-responsive"></div>');
                }
            });
        }


    });
