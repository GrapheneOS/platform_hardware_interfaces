/*
 * Copyright 2019 The Android Open Source Project
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#include <composer-vts/2.2/RenderEngineVts.h>
#include "renderengine/impl/ExternalTexture.h"

namespace android {
namespace hardware {
namespace graphics {
namespace composer {
namespace V2_2 {
namespace vts {

using renderengine::DisplaySettings;
using renderengine::LayerSettings;
using renderengine::RenderEngineCreationArgs;

TestRenderEngine::TestRenderEngine(const RenderEngineCreationArgs& args) {
    mFormat = static_cast<common::V1_1::PixelFormat>(args.pixelFormat);
    mRenderEngine = renderengine::RenderEngine::create(args);
}

TestRenderEngine::~TestRenderEngine() {
    mRenderEngine.release();
}

void TestRenderEngine::setRenderLayers(std::vector<std::shared_ptr<TestLayer>> layers) {
    sort(layers.begin(), layers.end(),
         [](const std::shared_ptr<TestLayer>& lhs, const std::shared_ptr<TestLayer>& rhs) -> bool {
             return lhs->mZOrder < rhs->mZOrder;
         });

    if (!mCompositionLayers.empty()) {
        mCompositionLayers.clear();
    }
    for (auto& layer : layers) {
        LayerSettings settings = layer->toRenderEngineLayerSettings();
        mCompositionLayers.push_back(settings);
    }
}

void TestRenderEngine::initGraphicBuffer(uint32_t width, uint32_t height, uint32_t layerCount,
                                         uint64_t usage) {
    mGraphicBuffer =
            new GraphicBuffer(width, height, static_cast<int32_t>(mFormat), layerCount, usage);
}

void TestRenderEngine::drawLayers() {
    base::unique_fd bufferFence;

    std::vector<renderengine::LayerSettings> compositionLayers;
    compositionLayers.reserve(mCompositionLayers.size());
    std::transform(mCompositionLayers.begin(), mCompositionLayers.end(),
                   std::back_insert_iterator(compositionLayers),
                   [](renderengine::LayerSettings& settings) -> renderengine::LayerSettings {
                       return settings;
                   });
    auto texture = std::make_shared<renderengine::impl::ExternalTexture>(
            mGraphicBuffer, *mRenderEngine, renderengine::impl::ExternalTexture::Usage::WRITEABLE);
    auto result = mRenderEngine
                          ->drawLayers(mDisplaySettings, compositionLayers, texture,
                                       std::move(bufferFence))
                          .get();
    if (result.ok()) {
        result.value()->waitForever(LOG_TAG);
    }
}

void TestRenderEngine::checkColorBuffer(std::vector<V2_2::IComposerClient::Color>& expectedColors) {
    void* bufferData;
    ASSERT_EQ(0, mGraphicBuffer->lock(mGraphicBuffer->getUsage(), &bufferData));
    ReadbackHelper::compareColorBuffers(expectedColors, bufferData, mGraphicBuffer->getStride(),
                                        mGraphicBuffer->getWidth(), mGraphicBuffer->getHeight(),
                                        mFormat);
    ASSERT_EQ(0, mGraphicBuffer->unlock());
}

}  // namespace vts
}  // namespace V2_2
}  // namespace composer
}  // namespace graphics
}  // namespace hardware
}  // namespace android
